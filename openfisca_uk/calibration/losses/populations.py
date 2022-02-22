from typing import Tuple
import numpy as np
import tensorflow as tf
from openfisca_uk.parameters import parameters
from openfisca_uk import Microsimulation
from openfisca_uk.calibration.losses.loss_category import LossCategory


class Populations(LossCategory):
    weight = 1
    label = "Population"
    parameter_folder = parameters.calibration.age_sex_region_populations

    @classmethod
    def compute(
        cls,
        sim: Microsimulation,
        household_weights: tf.Tensor,
        year: int,
        excluded_metrics: list,
    ) -> Tuple[tf.Tensor, dict]:
        """Calculates loss against population statistics.

        Args:
            sim (Microsimulation): Simulation with data on ages and household membership.
            household_weights (tf.Tensor): Per-household weights for the given year.
            year (int): The year to test against.
            excluded_metrics (list): Parameters to avoid testing.

        Raises:
            ValueError: If an unexpected parameter is found in the age-sex-region parameter tree.

        Returns:
            Tuple[tf.Tensor, dict]: The total loss, plus a dictionary with per-epoch results.
        """
        population_loss = 0
        logging_dict = {
            metric.name + "." + str(year): dict(model=[], loss=[])
            for metric in cls.get_metrics()
        }
        person_sex = sim.calc("gender")
        person_age = sim.calc("age")
        person_region = sim.calc("region", map_to="person")
        population = cls.parameter_folder
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
                    if parameter_name in excluded_metrics:
                        continue
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
                    logging_dict[parameter_name]["model"].append(
                        model_population.numpy()
                    )
                    l = (
                        model_population - parameter(f"{year}-01-01")
                    ) ** 2
                    population_loss += l
                    logging_dict[parameter_name]["loss"].append(
                        l.numpy()
                    )

        return population_loss, logging_dict
