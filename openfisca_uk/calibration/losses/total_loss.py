from typing import List
from openfisca_uk.calibration.losses.populations import Populations
from openfisca_uk.calibration.losses.households import Households
from openfisca_uk.calibration.losses.tenure_type import TenureType
from openfisca_uk.calibration.losses.council_tax_bands import (
    CouncilTaxBandHouseholds,
)
from random import sample
import tensorflow as tf

from openfisca_uk.tools.simulation import Microsimulation


class LossCalculator:
    def __init__(self, sim: Microsimulation, validation_split: float = 0.1):
        """A loss calculator with persistent validation separation.

        Args:
            sim (Microsimulation): A microsimulation from which to draw demographic data.
            validation_split (float, optional): Percentage of metrics to use as validation. Defaults to 0.1.
        """
        self.losses = [
            Populations,
            Households,
            TenureType,
            CouncilTaxBandHouseholds,
        ]
        self.validation_split = validation_split
        self.sim = sim
        self.training_log = []
        self.metrics = sum(
            [list(loss.get_metric_names()) for loss in self.losses], []
        )
        self.validation_metrics = sample(
            self.metrics, int(self.validation_split * len(self.metrics))
        )
        self.training_metrics = [
            metric
            for metric in self.metrics
            if metric not in self.validation_metrics
        ]

    def compute_loss(
        self,
        weight_changes: tf.Tensor,
        validation: bool = False,
        epoch: int = 0,
    ) -> tf.Tensor:
        """Computes loss for a given set of household weights.

        Args:
            weight_changes (tf.Tensor): Household weight changes for each year.
            validation (bool, optional): Whether to use validation or training metrics. Defaults to False.
            epoch (int, optional): The epoch number to record losses against. Defaults to 0.

        Returns:
            tf.Tensor: The total loss.
        """
        loss = 0
        for loss_category in self.losses:
            for year in range(2019, 2022):
                frs_weights = self.sim.calc("household_weight", year).values
                loss_category_loss, loss_category_log = loss_category.compute(
                    self.sim,
                    tf.nn.relu(frs_weights + weight_changes[year - 2019]),
                    year,
                    self.training_metrics
                    if validation
                    else self.validation_metrics,
                )
                loss += loss_category_loss
                self.training_log += [
                    dict(**entry, epoch=epoch, validation=validation)
                    for entry in loss_category_log
                ]
        return loss
