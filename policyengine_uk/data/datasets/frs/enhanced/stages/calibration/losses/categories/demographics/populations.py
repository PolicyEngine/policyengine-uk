from ...loss_category import LossCategory
from policyengine_uk.tools.simulation import Microsimulation
import tensorflow as tf
import numpy as np
from policyengine_core.parameters import ParameterNode, Parameter
from typing import Iterable, Tuple
from policyengine_uk.parameter_tree import parameters


class Populations(LossCategory):
    name = "Populations"
    category = "Populations"

    def initialise(self):
        self.people = self.sim.calc(
            "people", map_to="household", period=self.year
        ).values
        self.comparisons = []
        age = self.sim.calc("age").values
        sex = self.sim.calc("gender").values
        region = self.sim.calc("region", map_to="person").values
        age_sex_region = (
            self.calibration_parameters.demographics.populations.by_age_sex_region
        )
        total_population = 0
        for lower_age in list(range(0, 80, 10)) + [79]:
            meets_age_criteria = (age >= lower_age) & (age < lower_age + 10)
            age_population = 0
            age_string = (
                f"BETWEEN_{lower_age}_{lower_age + 10}"
                if lower_age < 79
                else "OVER_80"
            )
            for target_sex in ("MALE", "FEMALE"):
                age_sex_population = 0
                for target_region in self.sim.calc("region").unique():
                    meets_all_criteria = (
                        meets_age_criteria
                        & (region == target_region)
                        & (sex == target_sex)
                    )
                    actual_population = (
                        age_sex_region._children[target_sex]
                        ._children[target_region]
                        ._children[age_string]
                    )
                    self.comparisons += [
                        (
                            f"{target_region}_{target_sex}_{lower_age}_{lower_age + 10}",
                            self.sim.map_result(
                                meets_all_criteria, "person", "household"
                            ),
                            actual_population,
                        )
                    ]
                    age_sex_population += actual_population

                self.comparisons += [
                    (
                        f"{target_sex}_{lower_age}_{lower_age + 10}",
                        self.sim.map_result(
                            meets_age_criteria & (sex == target_sex),
                            "person",
                            "household",
                        ),
                        age_sex_population,
                    )
                ]

                age_population += age_sex_population

            self.comparisons += [
                (
                    f"{lower_age}_{lower_age + 10}",
                    self.sim.map_result(
                        meets_age_criteria, "person", "household"
                    ),
                    age_population,
                )
            ]

            total_population += age_population

        self.comparisons += [
            (
                f"people",
                self.sim.map_result(np.ones_like(age), "person", "household"),
                total_population,
            )
        ]

    def get_loss_subcomponents(
        self, household_weights: tf.Tensor
    ) -> Iterable[Tuple]:
        for name, values, target in self.comparisons:
            yield name, tf.reduce_sum(values * household_weights), target

    def get_metric_names(self) -> Iterable[str]:
        return [x[0] for x in self.comparisons]
