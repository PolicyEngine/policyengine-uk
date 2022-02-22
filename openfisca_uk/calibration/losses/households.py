from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import Microsimulation
from typing import List, Tuple
from openfisca_uk.parameters import parameters


class Households(LossCategory):
    weight = 1
    label = "Households"
    parameter_folder = parameters.calibration.households

    @classmethod
    def compute(
        cls,
        sim: Microsimulation,
        household_weights: tf.Tensor,
        year: int,
        excluded_metrics: list,
    ) -> Tuple[tf.Tensor, dict]:
        """Calculates loss against household statistics.

        Args:
            household_weights (tf.Tensor): Per-household weights for the given year.
            year (int): The year to test against.
            excluded_metrics (list): Parameters to avoid testing.

        Returns:
            Tuple[tf.Tensor, dict]: The total loss, plus a dictionary with per-epoch results.
        """

        household_loss = 0
        parameter = cls.parameter_folder
        parameter_name = parameter.name + "." + str(year)
        logging_dict = {parameter_name: dict(model=[], loss=[])}
        model_population = tf.reduce_sum(household_weights)
        logging_dict[parameter_name]["model"].append(model_population)
        if parameter_name not in excluded_metrics:
            household_loss += (
                model_population - parameter(f"{year}-01-01")
            ) ** 2

        return household_loss, logging_dict
