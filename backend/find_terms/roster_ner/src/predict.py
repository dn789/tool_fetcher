import torch
# import torch.nn.functional as F
from torch.utils.data import (
    DataLoader, SequentialSampler, TensorDataset)
from transformers import RobertaTokenizer
from tqdm import tqdm
from .model import RoSTERModel


class RoSTerPredictor(object):

    def __init__(self, model_type, dropout, entity_types, tag_scheme, max_seq_length, eval_batch_size):
        self.entity_types = entity_types
        self.model_type = model_type
        self.dropout = dropout
        self.tag_scheme = tag_scheme
        self.max_seq_length = max_seq_length
        self.eval_batch_size = eval_batch_size
        self.label_map, self.inv_label_map = self.get_label_map()
        self.num_labels = len(self.inv_label_map) - 1
        self.model = RoSTERModel.from_pretrained(self.model_type, num_labels=self.num_labels - 1,
                                                 hidden_dropout_prob=self.dropout, attention_probs_dropout_prob=self.dropout)
        self.tokenizer = RobertaTokenizer.from_pretrained(
            self.model_type, do_lower_case=False)
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        print(f"***** Using {torch.cuda.device_count()} GPU(s)! *****\n")
        if torch.cuda.device_count() > 1:
            self.multi_gpu = True
        else:
            self.multi_gpu = False

    def get_label_map(self):
        label_map = {'O': 0}
        num_labels = 1
        for entity_type in self.entity_types:
            label_map['B-' + entity_type] = num_labels
            if self.tag_scheme == 'iob':
                label_map['I-' + entity_type] = num_labels + 1
                num_labels += 2
            elif self.tag_scheme == 'io':
                label_map['I-' + entity_type] = num_labels
                num_labels += 1
        label_map['UNK'] = -100
        inv_label_map = {k: v for v, k in label_map.items()}
        self.label_map = label_map
        self.inv_label_map = inv_label_map
        return label_map, inv_label_map

    def drop_o(self, tensor_data, drop_o_ratio=0):
        if drop_o_ratio == 0:
            return tensor_data
        labels = tensor_data["all_labels"]
        rand_num = torch.rand(labels.size())
        drop_pos = (labels == 0) & (rand_num < drop_o_ratio)
        labels[drop_pos] = -100
        tensor_data["all_labels"] = labels
        return tensor_data

    def get_tensor(self, sents, max_seq_length, drop_o_ratio=0):
        all_data = []
        for sent in sents:
            all_data.append((sent, ['O' for word in sent.split()]))
        raw_labels = [data[1] for data in all_data]
        all_input_ids = []
        all_attention_mask = []
        all_labels = []
        all_valid_pos = []
        for text, labels in tqdm(all_data, desc="Converting to tensors"):
            encoded_dict = self.tokenizer.encode_plus(text, add_special_tokens=True, max_length=max_seq_length,
                                                      padding='max_length', return_attention_mask=True, truncation=True, return_tensors='pt')
            input_ids = encoded_dict['input_ids']
            attention_mask = encoded_dict['attention_mask']
            all_input_ids.append(input_ids)
            all_attention_mask.append(attention_mask)
            label_idx = -100 * torch.ones(max_seq_length, dtype=torch.long)
            valid_pos = torch.zeros(max_seq_length, dtype=torch.long)
            tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
            j = 0
            for i, token in enumerate(tokens[1:], start=1):  # skip [CLS]
                if token == self.tokenizer.sep_token:
                    break
                if i == 1 or token.startswith('Ġ'):
                    label = labels[j]
                    label_idx[i] = self.label_map[label]
                    valid_pos[i] = 1
                    j += 1
            assert j == len(labels) or i == max_seq_length - 1
            all_labels.append(label_idx.unsqueeze(0))
            all_valid_pos.append(valid_pos.unsqueeze(0))

        all_input_ids = torch.cat(all_input_ids, dim=0)
        all_attention_mask = torch.cat(all_attention_mask, dim=0)
        all_labels = torch.cat(all_labels, dim=0)
        all_valid_pos = torch.cat(all_valid_pos, dim=0)
        all_idx = torch.arange(all_input_ids.size(0))
        tensor_data = {"all_idx": all_idx, "all_input_ids": all_input_ids, "all_attention_mask": all_attention_mask,
                       "all_labels": all_labels, "all_valid_pos": all_valid_pos, "raw_labels": raw_labels}
        return self.drop_o(tensor_data, drop_o_ratio)
    # obtain model predictions on a given dataset

    def eval(self, sents):
        tensor_data = self.get_tensor(
            sents, max_seq_length=self.max_seq_length)

        all_idx = tensor_data["all_idx"]
        all_input_ids = tensor_data["all_input_ids"]
        all_attention_mask = tensor_data["all_attention_mask"]
        all_labels = tensor_data["all_labels"]
        all_valid_pos = tensor_data["all_valid_pos"]
        self.y_true = tensor_data["raw_labels"]

        eval_data = TensorDataset(
            all_idx, all_input_ids, all_attention_mask, all_valid_pos, all_labels)
        eval_sampler = SequentialSampler(eval_data)
        eval_dataloader = DataLoader(
            eval_data, sampler=eval_sampler, batch_size=self.eval_batch_size)

        # self.model = self.model.to(self.device)
        self.model.eval()
        y_pred = []
        pred_probs = []
        for batch in tqdm(eval_dataloader, desc="Evaluating"):
            _, input_ids, attention_mask, valid_pos, _ = tuple(
                t.to(self.device) for t in batch)

            max_len = attention_mask.sum(-1).max().item()
            input_ids, attention_mask, valid_pos = tuple(t[:, :max_len] for t in
                                                         (input_ids, attention_mask, valid_pos))

            with torch.no_grad():
                logits, bin_logits = self.model(
                    input_ids, attention_mask, valid_pos)
                entity_prob = torch.sigmoid(bin_logits)
                type_prob = torch.nn.functional.softmax(
                    logits, dim=-1) * entity_prob
                non_type_prob = 1 - entity_prob
                type_prob = torch.cat([non_type_prob, type_prob], dim=-1)

                preds = torch.argmax(type_prob, dim=-1)
                preds = preds.cpu().numpy()
                pred_prob = type_prob.cpu()

            num_valid_tokens = valid_pos.sum(dim=-1)
            i = 0
            for j in range(len(num_valid_tokens)):
                pred_probs.append(pred_prob[i:i + num_valid_tokens[j]])
                y_pred.append([self.inv_label_map[pred]
                              for pred in preds[i:i + num_valid_tokens[j]]])
                i += num_valid_tokens[j]

        return y_pred, pred_probs

    # load model from directory

    def load_model(self, model_dir):
        map_location = torch.device(
            'cpu') if self.device.type == 'cpu' else None
        self.model.load_state_dict(torch.load(
            model_dir, map_location=map_location))


def load_predictor(model_dir,
                   model_type='roberta-base',
                   entity_types=['Term'],

                   dropout=.1,
                   tag_scheme='iob',
                   max_seq_length=120,
                   eval_batch_size=64):
    predictor = RoSTerPredictor(model_type=model_type,
                                entity_types=entity_types,
                                dropout=dropout,
                                tag_scheme=tag_scheme,
                                max_seq_length=max_seq_length,
                                eval_batch_size=eval_batch_size)
    predictor.load_model(model_dir)
    # y_pred, _ = predictor.eval(predictor.model, predictor.eval_dataloader)
    return predictor
