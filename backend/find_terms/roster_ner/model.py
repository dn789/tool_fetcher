import math
from transformers import RobertaForTokenClassification
import torch


def gelu(x):
    """ Original Implementation of the gelu activation function in Google Bert repo when initially created.
        For information: OpenAI GPT's gelu is slightly different (and gives slightly different results):
        0.5 * x * (1 + torch.tanh(math.sqrt(2 / math.pi) * (x + 0.044715 * torch.pow(x, 3))))
        Also see https://arxiv.org/abs/1606.08415
    """
    return x * 0.5 * (1.0 + torch.erf(x / math.sqrt(2.0)))


class RobertaLMHead(torch.nn.Module):
    """Roberta Head for masked language modeling."""

    def __init__(self, config):
        super().__init__()
        self.dense = torch.nn.Linear(config.hidden_size, config.hidden_size)
        self.layer_norm = torch.nn.LayerNorm(
            config.hidden_size, eps=config.layer_norm_eps)

        self.decoder = torch.nn.Linear(config.hidden_size, config.vocab_size)
        self.bias = torch.nn.Parameter(torch.zeros(config.vocab_size))
        self.decoder.bias = self.bias

    def forward(self, features, **kwargs):
        x = self.dense(features)
        x = gelu(x)
        x = self.layer_norm(x)

        # project back to size of vocabulary with bias
        x = self.decoder(x)

        return x

    def _tie_weights(self):
        # To tie those two weights if they get disconnected (on TPU or when the bias is resized)
        # For accelerate compatibility and to not break backward compatibility
        if self.decoder.bias.device.type == "meta":
            self.decoder.bias = self.bias
        else:
            self.bias = self.decoder.bias


class RoSTERModel(RobertaForTokenClassification):

    def __init__(self, config):
        super().__init__(config)
        self.lm_head = RobertaLMHead(config)
        self.bin_classifier = torch.nn.Linear(config.hidden_size, 1)
        self.init_weights()
        for param in self.lm_head.parameters():
            param.requires_grad = False

    def forward(self, input_ids, attention_mask, valid_pos):
        sequence_output = self.roberta(
            input_ids, attention_mask=attention_mask)[0]
        valid_output = sequence_output[valid_pos > 0]
        sequence_output = self.dropout(valid_output)
        logits = self.classifier(sequence_output)
        bin_logits = self.bin_classifier(sequence_output)
        return logits, bin_logits

    def mlm_pred(self, input_ids, attention_mask, valid_pos):
        sequence_output = self.roberta(
            input_ids, attention_mask=attention_mask)[0]
        valid_output = sequence_output[valid_pos > 0]
        logits = self.lm_head(valid_output)
        return logits
