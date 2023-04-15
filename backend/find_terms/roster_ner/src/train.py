import shutil
from .trainer import RoSTERTrainer


def train(args):

    print(args)

    if args.do_train:

        # train K models for ensemble
        for i in range(args.num_models):
            trainer = RoSTERTrainer(args)
            trainer.noise_robust_train(i)
            args.seed = args.seed + 1

        # ensemble K model predictions and train an ensembled model
        trainer = RoSTERTrainer(args)
        trainer.ensemble_pred(trainer.temp_dir)
        trainer.ensemble_train()

        # self-training
        trainer.self_train()

        shutil.rmtree(trainer.temp_dir, ignore_errors=True)

    if args.do_eval:

        trainer = RoSTERTrainer(args)
        trainer.load_model("final_model.pt", args.output_dir)
        y_pred, _ = trainer.eval(trainer.model, trainer.eval_dataloader)
        trainer.performance_report(trainer.y_true, y_pred)
