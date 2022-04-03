from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import parameters


class HouseholdsInTotal(LossCategory):
    label = "Households in total"
    parameter_folder = parameters.calibration.households.in_total
    weight = 1 / 30

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        model_population = tf.reduce_sum(household_weights)
        actual_population = HouseholdsInTotal.parameter_folder(f"{year}-01-01")
        yield HouseholdsInTotal.parameter_folder.name + "." + str(
            year
        ), model_population, actual_population

    def get_metrics():
        return [HouseholdsInTotal.parameter_folder]

    def get_metric_names():
        return [
            HouseholdsInTotal.parameter_folder.name + "." + str(year)
            for year in range(2019, 2027)
        ]
