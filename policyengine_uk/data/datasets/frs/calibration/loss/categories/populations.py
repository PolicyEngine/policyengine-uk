from survey_enhance.reweight import LossCategory
from policyengine_core.data import Dataset
from ..utils import sum_by_household
import torch
from typing import List, Tuple
import numpy as np


class Populations(LossCategory):
    weight = 1
    static_dataset = False

    def get_comparisons(
        self, dataset: Dataset
    ) -> List[Tuple[str, float, torch.Tensor]]:
        comparisons = []
        age = dataset.person.age
        sex = dataset.person.gender
        region = dataset.person.region
        age_sex_region = (
            self.calibration_parameters_at_instant.demographics.populations.by_age_sex_region
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
                for target_region in region.unique():
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
                    comparisons += [
                        (
                            f"{target_region}_{target_sex}_{lower_age}_{lower_age + 10}",
                            sum_by_household(meets_all_criteria, dataset),
                            actual_population,
                        )
                    ]
                    age_sex_population += actual_population

                comparisons += [
                    (
                        f"{target_sex}_{lower_age}_{lower_age + 10}",
                        sum_by_household(
                            meets_age_criteria & (sex == target_sex),
                            dataset,
                        ),
                        age_sex_population,
                    )
                ]

                age_population += age_sex_population

            comparisons += [
                (
                    f"{lower_age}_{lower_age + 10}",
                    sum_by_household(
                        meets_age_criteria,
                        dataset,
                    ),
                    age_population,
                )
            ]

            total_population += age_population

        comparisons += [
            (
                f"people",
                sum_by_household(np.ones_like(age), dataset),
                total_population,
            )
        ]

        return comparisons
