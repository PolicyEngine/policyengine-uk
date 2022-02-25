from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk.parameters import parameters


class Households(LossCategory):
    weight = 1
    label = "Households"
    parameter_folder = parameters.calibration.households

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        model_population = tf.reduce_sum(household_weights)
        actual_population = Households.parameter_folder(f"{year}-01-01")
        yield Households.parameter_folder.name + "." + str(
            year
        ), model_population, actual_population

    def get_metrics():
        return [Households.parameter_folder]

    def get_metric_names():
        return [
            Households.parameter_folder.name + "." + str(year)
            for year in range(2019, 2023)
        ]
