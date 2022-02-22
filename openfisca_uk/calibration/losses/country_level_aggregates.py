from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import Microsimulation
from typing import List, Tuple
from openfisca_uk.parameters import parameters


class CountryLevelAggregates(LossCategory):
    weight = 1
    label = "Country-level aggregates"
    parameter_folder = parameters.calibration.households

    @classmethod
    def compute(
        cls,
        sim: Microsimulation,
        household_weights: tf.Tensor,
        year: int,
        excluded_metrics: list,
    ) -> Tuple[tf.Tensor, dict]:
        pass
