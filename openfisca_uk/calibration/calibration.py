import tensorflow as tf
import numpy as np
from openfisca_uk import Microsimulation
from openfisca_uk.calibration.losses.total_loss import LossCalculator


class HouseholdWeights:
    def __init__(self, start_year: int = 2019, end_year: int = 2022):
        self.start_year = start_year
        self.end_year = end_year

    def calibrate(
        self,
        sim: Microsimulation,
        validation_split: float = 0.1,
        num_epochs: int = 256,
        learning_rate: float = 1e-3,
    ):
        """Calibrate FRS weights to administrative statistics.

        Args:
            sim (Microsimulation): A simulation containing demographic variables.
            validation_split (float, optional): The percentage of metrics to use as validation. Defaults to 0.1.
            num_epochs (int, optional): The number of epochs to run. Defaults to 256.
            learning_rate (float, optional): The learning rate for the optimiser. Defaults to 1e-3.
        """

        survey_num_households = len(sim.calc("household_id"))
        self.weight_changes = tf.Variable(
            np.zeros(
                (self.end_year + 1 - self.start_year, survey_num_households)
            ),
            dtype=tf.float32,
        )
        opt = tf.keras.optimizers.Adam(learning_rate=learning_rate)
        loss_calculator = LossCalculator(sim, validation_split)
        for epoch in range(num_epochs):
            with tf.GradientTape() as tape:
                loss = loss_calculator.compute_loss(
                    self.weight_changes, validation=False, epoch=epoch
                )
            grads = tape.gradient(loss, self.weight_changes)
            validation_loss = loss_calculator.compute_loss(
                self.weight_changes, validation=True, epoch=epoch
            )
            opt.apply_gradients(zip(grads, self.weight_changes))
            print(
                f"Epoch {epoch}: loss={loss.numpy():.4f}, validation_loss={validation_loss.numpy():.4f}"
            )


if __name__ == "__main__":
    weights = HouseholdWeights()
    weights.calibrate()
