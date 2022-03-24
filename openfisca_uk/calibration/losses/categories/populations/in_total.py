from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import parameters


class PopulationsInTotal(LossCategory):
    label = "UK population"
    parameter_folder = parameters.calibration.populations.in_total

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        num_people = sim.calc("people", map_to="household").values
        model_population = tf.reduce_sum(household_weights * num_people)
        actual_population = PopulationsInTotal.parameter_folder(
            f"{year}-01-01"
        )
        yield PopulationsInTotal.parameter_folder.name + "." + str(
            year
        ), model_population, actual_population

    def get_metrics():
        return [PopulationsInTotal.parameter_folder]

    def get_metric_names():
        return [
            PopulationsInTotal.parameter_folder.name + "." + str(year)
            for year in range(2019, 2023)
        ]
