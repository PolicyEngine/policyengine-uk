from typing import Tuple
import tensorflow as tf
from openfisca_uk import Microsimulation
from openfisca_uk.parameters import parameters
from openfisca_uk.calibration.losses.loss_category import LossCategory


class CouncilTaxBandHouseholds(LossCategory):
    weight = 1
    label = "Council Tax Band Households"
    parameter_folder = parameters.calibration.council_tax_band_counts

    @classmethod
    def compute(
        cls,
        sim: Microsimulation,
        household_weights: tf.Tensor,
        year: int,
        excluded_metrics: list,
    ) -> Tuple[tf.Tensor, dict]:
        """Calculates loss against Council Tax band statistics.

        Args:
            sim (Microsimulation): Microsimulation from which to draw council tax bands.
            household_weights (tf.Tensor): Per-household weights.
            year (int): The time period to test over.
            excluded_metrics (list): A list of excluded parameters to ignore.

        Returns:
            Tuple[tf.Tensor, dict]: The total loss, plus a dictionary with per-epoch results.
        """
        population_loss = 0
        logging_dict = {
            metric.name + "." + str(year): dict(model=[], loss=[])
            for metric in ct_bands
        }
        ct_band = sim.calc("council_tax_band")
        ct_bands = cls.parameter_folder
        for region in ct_bands.children:
            for band in ct_bands.children[region].children:
                parameter = ct_bands.children[region].children[band]
                parameter_name = parameter.name + "." + str(year)
                if parameter_name in excluded_metrics:
                    continue
                model_population = tf.reduce_sum(
                    (ct_band == band) * household_weights
                )
                logging_dict[parameter_name]["model"].append(model_population)
                population_loss += (
                    model_population - parameter(f"{year}-01-01")
                ) ** 2

        return population_loss, logging_dict
