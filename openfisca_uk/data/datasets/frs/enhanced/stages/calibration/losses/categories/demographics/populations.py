from ...loss_category import LossCategory
from openfisca_uk.tools.simulation import Microsimulation
import tensorflow as tf
import numpy as np
from openfisca_core.parameters import ParameterNode, Parameter
from typing import Iterable, Tuple
from openfisca_uk.parameters import parameters


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
        for lower_age in list(range(0, 80, 10)) + [79]:
            age_string = (
                f"BETWEEN_{lower_age}_{lower_age + 10}"
                if lower_age < 79
                else "OVER_80"
            )
            for target_sex in ("MALE", "FEMALE"):
                for target_region in self.sim.calc("region").unique():
                    meets_age_criteria = (age >= lower_age) & (
                        age < lower_age + 10
                    )
                    meets_all_criteria = (
                        meets_age_criteria
                        & (region == target_region)
                        & (sex == target_sex)
                    )
                    self.comparisons += [
                        (
                            f"{target_region}_{target_sex}_{lower_age}_{lower_age + 10}",
                            self.sim.map_to(
                                meets_all_criteria, "person", "household"
                            ),
                            age_sex_region._children[target_sex]
                            ._children[target_region]
                            ._children[age_string],
                        )
                    ]

    def get_loss_subcomponents(
        self, household_weights: tf.Tensor
    ) -> Iterable[Tuple]:
        for name, values, target in self.comparisons:
            yield name, tf.reduce_sum(values * household_weights), target

    def get_metric_names(self) -> Iterable[str]:
        return [x[0] for x in self.comparisons]
