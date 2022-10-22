from glob import glob
import os
from time import time
import tensorflow as tf
import numpy as np
from policyengine_uk.data.datasets.frs.enhanced.stages.calibration.calibrated_frs import (
    CalibratedFRS,
)
from policyengine_uk.data.datasets.frs.frs import FRS
from policyengine_uk.data.storage import policyengine_uk_MICRODATA_FOLDER
from policyengine_uk.tools.simulation import Microsimulation
from policyengine_uk.repo import REPO
from policyengine_uk.data.datasets.frs.enhanced.stages.calibration.losses import (
    LossCalculator,
)
from pathlib import Path
import h5py
import pandas as pd
from argparse import ArgumentParser
from policyengine_core.data import Dataset


class HouseholdWeights:
    def __init__(self, start_year: int = 2022, end_year: int = 2027):
        self.start_year = start_year
        self.end_year = end_year

    def calibrate(
        self,
        validation_split: float = 0.1,
        num_epochs: int = 32,
        learning_rate: float = 1e1,
        loss_calculator: LossCalculator = None,
        dataset: Dataset = FRS,
    ):
        """Calibrate FRS weights to administrative statistics.

        Args:
            sim (Microsimulation): A simulation containing demographic variables.
            validation_split (float, optional): The percentage of metrics to use as validation. Defaults to 0.1.
            num_epochs (int, optional): The number of epochs to run. Defaults to 256.
            learning_rate (float, optional): The learning rate for the optimiser. Defaults to 8e+1.
            loss_calculator (LossCalculator, optional): A loss calculator to use. Defaults to None.
            dataset (Dataset, optional): The dataset to use. Defaults to FRS.
        """
        self.sim = (
            loss_calculator.sim
            if loss_calculator is not None
            else Microsimulation(dataset=dataset, average_parameters=True)
        )
        survey_num_households = len(self.sim.calc("household_id"))
        self.weight_changes = tf.Variable(
            np.ones(
                (self.end_year + 1 - self.start_year, survey_num_households)
            ),
            dtype=tf.float32,
        )
        opt = tf.keras.optimizers.Adam(learning_rate=learning_rate)
        loss_calculator = loss_calculator or LossCalculator(
            self.sim,
            validation_split,
            start_year=self.start_year,
            end_year=self.end_year,
        )
        start_train_loss = None
        start_val_loss = None
        start_time = time()
        for epoch in range(num_epochs):
            with tf.GradientTape() as tape:
                loss = loss_calculator.compute_loss(
                    self.weight_changes, validation=False, epoch=epoch
                )
                grads = tape.gradient(loss, self.weight_changes)
            if validation_split > 0:
                validation_loss = loss_calculator.compute_loss(
                    self.weight_changes, validation=True, epoch=epoch
                )
            else:
                validation_loss = tf.constant(0, dtype=tf.float32)
            if start_train_loss is None:
                start_train_loss = loss.numpy()
            if start_val_loss is None:
                start_val_loss = validation_loss.numpy()
            opt.apply_gradients(zip([grads], [self.weight_changes]))
            seconds_elapsed = time() - start_time
            hours = seconds_elapsed // 3600
            minutes = (seconds_elapsed - hours * 3600) // 60
            seconds = seconds_elapsed - hours * 3600 - minutes * 60
            time_str = f"{epoch + 1}/{num_epochs} ({int(hours)}h {int(minutes)}m {int(seconds)}s)"
            print(
                f"{time_str}, train loss = {loss.numpy() / start_train_loss - 1:.4%}, validation_loss = {validation_loss.numpy() / start_val_loss - 1:.4%}, train + validation loss = {(loss.numpy() + validation_loss.numpy()) / (start_train_loss + start_val_loss) - 1:.4%}"
            )
            if epoch > 0 and epoch % 20 == 0:
                self.training_log = loss_calculator.training_log
                self.save()

        self.training_log = loss_calculator.training_log

    def get_weights(self, year: int):
        return np.maximum(
            0,
            self.sim.calc("household_weight", period=year).values
            + self.weight_changes[year - self.start_year],
        )

    def get_microsimulation(self):
        sim_reweighted = Microsimulation(adjust_weights=False)
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

    def save(
        self, folder: Path = policyengine_uk_MICRODATA_FOLDER, run_id: str = 1
    ):
        if isinstance(folder, str):
            folder = Path(folder)

        for period in range(self.start_year, self.end_year + 1):
            CalibratedFRS.save(
                self.start_year,
                f"household_weight/{period}",
                self.get_weights(period),
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
        default=500,
        help="Number of epochs to run",
    )
    parser.add_argument(
        "--validation-split",
        type=float,
        default=0.0,
        help="Percentage of metrics to use as validation",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=1e3,
        help="Learning rate for optimiser",
    )
    parser.add_argument(
        "--k-fold-cross-validation",
        type=int,
        default=1,
        help="Number of folds for k-fold cross validation",
    )
    args = parser.parse_args()

    if args.k_fold_cross_validation > 1:
        sim = Microsimulation(average_parameters=True, adjust_weights=False)
        loss_calculators = LossCalculator.create_k_fold_cv_calculators(
            sim, k=args.k_fold_cross_validation
        )
        for i in range(args.k_fold_cross_validation):
            print(f"Running fold {i + 1}/{args.k_fold_cross_validation}")
            weights = HouseholdWeights()
            weights.calibrate(
                num_epochs=args.epochs,
                validation_split=args.validation_split,
                learning_rate=args.learning_rate,
                loss_calculator=loss_calculators[i],
            )
            weights.save(run_id=i + 1)
        print("Combining individual fold logs")
        logs = pd.concat(
            [
                pd.read_csv(
                    REPO / "calibration" / f"training_log_run_{i + 1}.csv"
                )
                for i in range(args.k_fold_cross_validation)
            ]
        )
        logs.sort_values(["run_id", "epoch", "category", "validation"]).to_csv(
            REPO / "calibration" / "training_log.csv", index=False
        )
        for filename in glob(
            (REPO / "calibration" / "training_log_run_*.csv").as_posix()
        ):
            os.remove(filename)
    else:
        weights = HouseholdWeights()
        weights.calibrate(
            num_epochs=args.epochs,
            validation_split=args.validation_split,
            learning_rate=args.learning_rate,
        )
        weights.save()
    print("Calibration completed.")
