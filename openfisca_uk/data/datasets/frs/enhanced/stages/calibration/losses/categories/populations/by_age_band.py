import numpy as np

from openfisca_uk.data.datasets.frs.enhanced.stages.calibration.losses.loss_category import (
    LossCategory,
)
import tensorflow as tf
from openfisca_uk.parameters import parameters
from openfisca_core.parameters import Parameter


class PopulationsByAgeBand(LossCategory):
    label = "Populations by age band"
    parameter_folder = parameters.calibration.populations.by_age_band
    weight = 1 / 20

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        total_population = parameters.calibration.populations.in_total(
            f"{year}-01-01"
        )
        total_age_bands = sum(
            [
                parameter(f"{year}-01-01")
                for parameter in PopulationsByAgeBand.parameter_folder.get_descendants()
                if isinstance(parameter, Parameter)
            ]
        )
        adjustment = total_population / total_age_bands
        population = PopulationsByAgeBand.parameter_folder
        person_age = sim.calc("age", year)
        for age_group in population.children:
            if "BETWEEN" in age_group:
                _, lower, upper = age_group.split("_")
                lower, upper = int(lower), int(upper)
            elif "OVER" in age_group:
                lower, upper = int(age_group.split("_")[1]) - 1, np.inf
            else:
                raise ValueError(f"Unexpected test group: {age_group}")
            people_in_household = sim.map_to(
                (person_age >= lower) * (person_age < upper),
                "person",
                "household",
            )
            model_population = tf.reduce_sum(
                people_in_household * household_weights
            )
            yield getattr(
                PopulationsByAgeBand.parameter_folder,
                age_group,
            ).name + "." + str(year), model_population, population.children[
                age_group
            ](
                f"{year}-01-01"
            ) * adjustment

    def get_metrics():
        return PopulationsByAgeBand.parameter_folder.get_descendants()

    def get_metric_names():
        return [
            parameter.name + "." + str(year)
            for year in range(2022, 2027)
            for parameter in PopulationsByAgeBand.get_metrics()
        ]
