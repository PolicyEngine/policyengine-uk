from ..loss_category import LossCategory
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
        self.people = self.sim.calc("people", map_to="household", period=self.year).values
        self.people_in_age_sex_region_bands = {}
        age = self.sim.calc("age").values
        sex = self.sim.calc("gender").values
        region = self.sim.calc("region", map_to="person").values
        self.targets_in_age_sex_region_bands = {}
        age_sex_region = parameters.calibration.populations.by_age_sex_region
        for lower_age in list(range(0, 80, 10)) + [79]:
            age_string = f"BETWEEN_{lower_age}_{lower_age + 10}" if lower_age < 79 else "OVER_80"
            for target_sex in ("MALE", "FEMALE"):
                for target_region in self.sim.calc("region").unique():
                    meets_age_criteria = (age >= lower_age) & (age < lower_age + 10)
                    meets_all_criteria = meets_age_criteria & (region == target_region) & (sex == target_sex)
                    self.people_in_age_sex_region_bands[(lower_age, target_sex, target_region)] = self.sim.map_to(meets_all_criteria, "person", "household")
                    self.targets_in_age_sex_region_bands[(lower_age, target_sex, target_region)] = age_sex_region.children[target_sex].children[target_region].children[age_string](f"{self.year}-01-01")

    def get_loss_subcomponents(self, household_weights: tf.Tensor) -> Iterable[Tuple]:
        for age, sex, region in self.targets_in_age_sex_region_bands:
            yield (
                f"{region}_{sex}_{age}-{age + 10}", 
                tf.reduce_sum(self.people_in_age_sex_region_bands[(age, sex, region)] * household_weights), 
                self.targets_in_age_sex_region_bands[(age, sex, region)],
            )