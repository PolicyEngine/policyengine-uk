import numpy as np
from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import parameters
from openfisca_core.parameters import Parameter


class PopulationsByAgeBand(LossCategory):
    label = "Populations by age band"
    parameter_folder = parameters.calibration.populations.by_age_sex_region
    weight = 1 / 30

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
        age_groups = {}
        for sex in population.children:
            for region in population.children[sex].children:
                for age_group in (
                    population.children[sex].children[region].children
                ):
                    parameter = (
                        population.children[sex]
                        .children[region]
                        .children[age_group]
                    )
                    if age_group not in age_groups:
                        age_groups[age_group] = parameter(f"{year}-01-01")
                    else:
                        age_groups[age_group] += parameter(f"{year}-01-01")
        for age_group in age_groups:
            if "BETWEEN" in age_group:
                _, lower, upper = age_group.split("_")
                lower, upper = int(lower), int(upper)
            elif "OVER" in age_group:
                lower, upper = int(age_group.split("_")[1]), np.inf
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
            if people_in_household.sum() > 0:
                # If the FRS has no observations, skip the target.
                yield getattr(
                    PopulationsByAgeBand.parameter_folder.MALE.LONDON,
                    age_group,
                ).name + "." + str(year), model_population, age_groups[
                    age_group
                ] * adjustment

    def get_metrics():
        return (
            PopulationsByAgeBand.parameter_folder.MALE.LONDON.get_descendants()
        )

    def get_metric_names():
        return [
            parameter.name + "." + str(year)
            for year in range(2019, 2027)
            for parameter in PopulationsByAgeBand.get_metrics()
        ]
