import tensorflow as tf
import numpy as np
from openfisca_uk import Microsimulation, REPO
from openfisca_uk.calibration.losses import LossCalculator
from pathlib import Path
import h5py
import pandas as pd


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
            print(
                f"Epoch {epoch}: train loss = {loss.numpy() / start_train_loss - 1:.2%}, validation_loss = {validation_loss.numpy() / start_val_loss - 1:.2%}"
            )

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

    def save(self, folder: Path = REPO / "calibration"):
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
        log.to_csv(folder / "training_log.csv", index=False)


if __name__ == "__main__":
    weights = HouseholdWeights()
    weights.calibrate(num_epochs=32)
    weights.save()
