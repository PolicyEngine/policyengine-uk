from time import time
import tensorflow as tf
import numpy as np
from openfisca_uk import Microsimulation, REPO
from openfisca_uk.calibration.losses import LossCalculator
from pathlib import Path
import h5py
import pandas as pd
from argparse import ArgumentParser


class HouseholdWeights:
    def __init__(self, start_year: int = 2019, end_year: int = 2022):
        self.start_year = start_year
        self.end_year = end_year

    def calibrate(
        self,
        validation_split: float = 0.1,
        num_epochs: int = 32,
        learning_rate: float = 1e1,
    ):
        """Calibrate FRS weights to administrative statistics.

        Args:
            sim (Microsimulation): A simulation containing demographic variables.
            validation_split (float, optional): The percentage of metrics to use as validation. Defaults to 0.1.
            num_epochs (int, optional): The number of epochs to run. Defaults to 256.
            learning_rate (float, optional): The learning rate for the optimiser. Defaults to 8e+1.
        """
        self.sim = Microsimulation(adjust_weights=False, duplicate_records=2)
        survey_num_households = len(self.sim.calc("household_id"))
        self.weight_changes = tf.Variable(
            np.zeros(
                (self.end_year + 1 - self.start_year, survey_num_households)
            ),
            dtype=tf.float32,
        )
        opt = tf.keras.optimizers.Adam(learning_rate=learning_rate)
        loss_calculator = LossCalculator(self.sim, validation_split)
        start_train_loss = None
        start_val_loss = None
        start_time = time()
        for epoch in range(num_epochs):
            with tf.GradientTape() as tape:
                loss = loss_calculator.compute_loss(
                    self.weight_changes, validation=False, epoch=epoch
                )
                grads = tape.gradient(loss, self.weight_changes)
            validation_loss = loss_calculator.compute_loss(
                self.weight_changes, validation=True, epoch=epoch
            )
            if start_train_loss is None:
                start_train_loss = loss.numpy()
            if start_val_loss is None:
                start_val_loss = validation_loss.numpy()
            opt.apply_gradients(zip([grads], [self.weight_changes]))
            time_str = f"{epoch + 1}/{num_epochs} ({time() - start_time:.2f}s)"
            print(
                f"{time_str}, train loss = {loss.numpy() / start_train_loss - 1:.4%}, validation_loss = {validation_loss.numpy() / start_val_loss - 1:.4%}, train + validation loss = {(loss.numpy() + validation_loss.numpy()) / (start_train_loss + start_val_loss) - 1:.4%}"
            )
            if epoch > 0 and epoch % 50 == 0:
                self.training_log = loss_calculator.training_log
                self.save()

        self.training_log = loss_calculator.training_log

    def get_microsimulation(self):
        sim_reweighted = Microsimulation(
            adjust_weights=False, duplicate_records=2
        )
        for year in range(self.start_year, self.end_year + 1):
            new_weights = np.maximum(
                0,
                self.sim.calc("household_weight", period=year).values
                + self.weight_changes[year - self.start_year],
            )
            sim_reweighted.set_input(
                "household_weight",
                year,
                new_weights,
            )
        return sim_reweighted

    def save(self, folder: Path = REPO / "calibration", run_id: str = 1):
        if isinstance(folder, str):
            folder = Path(folder)

        sim = self.get_microsimulation()

        with h5py.File(folder / "frs_weights.h5", "w") as f:
            for year in range(self.start_year, self.end_year + 1):
                f.create_dataset(
                    f"{year}",
                    data=sim.calc("household_weight", period=year).values,
                )

        log = pd.DataFrame(self.training_log)
        log["run_id"] = run_id
        log.to_csv(folder / f"training_log_run_{run_id}.csv", index=False)


if __name__ == "__main__":
    parser = ArgumentParser()
    # Arguments for epochs, validation split and learning rate
    parser.add_argument(
        "--epochs",
        type=int,
        default=32,
        help="Number of epochs to run",
    )
    parser.add_argument(
        "--validation-split",
        type=float,
        default=0.1,
        help="Percentage of metrics to use as validation",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e-2,
        help="Learning rate for optimiser",
    )
    parser.add_argument(
        "--k-fold-cross-validation",
        type=int,
        default=1,
        help="Number of folds for k-fold cross validation",
    )
    args = parser.parse_args()

    for i in range(args.k_fold_cross_validation):
        print(f"Running fold {i + 1}/{args.k_fold_cross_validation}")
        weights = HouseholdWeights()
        weights.calibrate(
            num_epochs=args.epochs,
            validation_split=args.validation_split,
            learning_rate=args.learning_rate,
        )
        weights.save(run_id=i + 1)
