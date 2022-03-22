from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import parameters


class FamiliesInTotal(LossCategory):
    label = "Families in total"
    parameter_folder = parameters.calibration.families.in_total

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        num_families = sim.calc("families", map_to="household").values
        model_population = tf.reduce_sum(household_weights * num_families)
        actual_population = FamiliesInTotal.parameter_folder(f"{year}-01-01")
        yield FamiliesInTotal.parameter_folder.name + "." + str(
            year
        ), model_population, actual_population

    def get_metrics():
        return [FamiliesInTotal.parameter_folder]

    def get_metric_names():
        return [
            FamiliesInTotal.parameter_folder.name + "." + str(year)
            for year in range(2019, 2023)
        ]
