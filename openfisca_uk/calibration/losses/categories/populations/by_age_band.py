import numpy as np
from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk.parameters import parameters


class AgeBands(LossCategory):
    weight = 1
    label = "Households"
    parameter_folder = parameters.calibration.age_sex_region_populations

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        population = AgeBands.parameter_folder
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
                lower, upper = float(lower), float(upper)
            elif "OVER" in age_group:
                lower, upper = float(age_group.split("_")[1]), np.inf
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
                AgeBands.parameter_folder.MALE.LONDON, age_group
            ).name, model_population, age_groups[age_group]

    def get_metrics():
        return [AgeBands.parameter_folder.MALE.LONDON.get_descendants()]

    def get_metric_names():
        return [
            parameter.name.name + "." + str(year)
            for year in range(2019, 2023)
            for parameter in AgeBands.get_metrics()
        ]
