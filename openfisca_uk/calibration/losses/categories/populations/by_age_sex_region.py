from random import random
import numpy as np
import tensorflow as tf
from openfisca_uk import parameters
from openfisca_uk.calibration.losses.loss_category import LossCategory


class PopulationsByAgeSexRegion(LossCategory):
    label = "Population by age, sex and region"
    parameter_folder = parameters.calibration.populations.by_age_sex_region

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        person_sex = sim.calc("gender").values
        person_age = sim.calc("age").values
        person_region = sim.calc("region", map_to="person").values
        population = PopulationsByAgeSexRegion.parameter_folder
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
                    parameter_name = parameter.name + "." + str(year)
                    if "BETWEEN" in age_group:
                        _, lower, upper = age_group.split("_")
                        lower, upper = float(lower), float(upper)
                    elif "OVER" in age_group:
                        lower, upper = float(age_group.split("_")[1]), np.inf
                    else:
                        raise ValueError(
                            f"Unexpected test group: {parameter_name}"
                        )
                    people_in_household = sim.map_to(
                        (person_sex == sex)
                        * (person_age >= lower)
                        * (person_age < upper)
                        * (person_region == region),
                        "person",
                        "household",
                    )
                    model_population = tf.reduce_sum(
                        people_in_household * household_weights
                    )
                    actual_population = parameter(f"{year}-01-01")
                    if people_in_household.sum() > 0:
                        # If the FRS has no observations, skip the target.
                        yield parameter_name, model_population, actual_population
