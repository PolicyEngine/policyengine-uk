from typing import List
import numpy as np
from .categories import Programs, Demographics
from random import sample
import tensorflow as tf
from policyengine_uk.tools.simulation import Microsimulation


class LossCalculator:
    def __init__(
        self,
        sim: Microsimulation,
        validation_split: float = 0.1,
        start_year: int = 2022,
        end_year: int = 2027,
    ):
        """A loss calculator with persistent validation separation.

        Args:
            sim (Microsimulation): A microsimulation from which to draw demographic data.
            validation_split (float, optional): Percentage of non-population metrics to use as validation. Defaults to 0.1.
            start_year (int, optional): The first year to use in the loss calculation. Defaults to 2022.
            end_year (int, optional): The last year to use in the loss calculation. Defaults to 2027.
        """
        loss_classes = [Programs, Demographics]
        self.losses = []
        years = list(range(start_year, end_year + 1))
        for loss_category in loss_classes:
            for year in years:
                self.losses.append(
                    loss_category(
                        years=years,
                        year=year,
                        weight=loss_category.weight,
                        sim=sim,
                    )
                )
        self.start_year = start_year
        self.end_year = end_year
        self.validation_split = validation_split
        self.sim = sim
        self.training_log = []
        self.metrics = sum(
            [list(loss.get_metric_names()) for loss in self.losses], []
        )
        TRAINING_ONLY_CATEGORIES = [
            "Demographics",
        ]
        non_population_metrics = sum(
            [
                list(loss.get_metric_names())
                for loss in self.losses
                if loss.name not in TRAINING_ONLY_CATEGORIES
            ],
            [],
        )
        self.validation_metrics = sample(
            non_population_metrics,
            int(self.validation_split * len(non_population_metrics)),
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
        loss = tf.constant(0, dtype=tf.float32)
        frs_weights = np.array(
            [
                self.sim.calc("household_weight", year).values
                for year in range(self.start_year, self.end_year + 1)
            ]
        )
        adjusted_weights = tf.nn.relu(frs_weights + weight_changes)
        for loss_category in self.losses:
            excluded_metrics = (
                self.training_metrics
                if validation
                else self.validation_metrics
            )
            loss_category_loss, loss_category_log = loss_category.compute(
                self.sim,
                adjusted_weights,
                excluded_metrics,
                validation,
            )
            loss += loss_category_loss
            self.training_log += [
                dict(**entry, epoch=epoch, validation=validation)
                for entry in loss_category_log
            ]
        return loss

    @staticmethod
    def create_k_fold_cv_calculators(sim: Microsimulation, k: int = 1) -> list:
        """Creates a list of loss calculators for k-fold cross validation.

        Args:
            sim (Microsimulation): A microsimulation from which to draw demographic data.
            k (int, optional): The number of folds (results in validation splits of 1 / k). Defaults to 1.

        Returns:
            List[LossCalculator]: The list of loss calculators.
        """
        base_calculator = LossCalculator(sim, validation_split=1)
        loss_calculators = [LossCalculator(sim) for _ in range(k)]
        for calculator in loss_calculators:
            calculator.validation_metrics = []
        for metric_name in base_calculator.validation_metrics:
            # For each metric, randomly select a training run in which to use
            # it as a validation metric.
            loss_calculators[sample(range(k), 1)[0]].validation_metrics.append(
                metric_name
            )
        return loss_calculators
