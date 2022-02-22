from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import Microsimulation
from typing import List, Tuple
from openfisca_uk.parameters import parameters


class TenureType(LossCategory):
    weight = 1
    label = "Tenure type"
    parameter_folder = parameters.calibration.tenure_type

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
            sim (Microsimulation): Simulation from which to draw tenure type data.
            household_weights (tf.Tensor): Per-household weights for the given year.
            year (int): The year to test against.
            excluded_metrics (list): Parameters to avoid testing.

        Returns:
            Tuple[tf.Tensor, dict]: The total loss, plus a dictionary with per-epoch results.
        """

        population_loss = 0
        logging_dict = {
            metric.name + "." + str(year): dict(model=[], loss=[])
            for metric in cls.get_metrics()
        }
        tenure_type = sim.calc("ons_tenure_type")
        tenure_metrics = cls.parameter_folder
        for region in tenure_metrics.children:
            for tenure in tenure_metrics.children[region].children:
                parameter = tenure_metrics.children[region].children[tenure]
                parameter_name = parameter.name + "." + str(year)
                if parameter_name in excluded_metrics:
                    continue
                model_population = tf.reduce_sum(
                    (tenure_type == tenure) * household_weights
                )
                logging_dict[parameter_name]["model"].append(model_population.numpy())
                l = (
                    model_population - parameter(f"{year}-01-01")
                ) ** 2
                logging_dict[parameter_name]["loss"].append(l.numpy())
                population_loss += l

        return population_loss, logging_dict
