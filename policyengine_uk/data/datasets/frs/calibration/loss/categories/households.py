from survey_enhance.reweight import LossCategory
from policyengine_core.data import Dataset
import torch
from typing import List, Tuple
import numpy as np


class Households(LossCategory):
    weight = 1
    static_dataset = False

    def get_comparisons(
        self, dataset: Dataset
    ) -> List[Tuple[str, float, torch.Tensor]]:
        region_ct_band_parameter = (
            self.calibration_parameters_at_instant.demographics.households.by_region_by_council_tax_band
        )

        uk_wide = (
            self.calibration_parameters_at_instant.demographics.households.in_total
        )

        comparisons = []

        ct_band = dataset.household.council_tax_band
        region = dataset.household.region
        country = dataset.household.country

        # Region - CT band

        total_actuals = 0

        for target_region in region_ct_band_parameter._children:
            for target_ct_band in region_ct_band_parameter._children[
                target_region
            ]._children:
                total_actuals += region_ct_band_parameter._children[
                    target_region
                ]._children[target_ct_band]

        region_ct_band_adjustment = uk_wide / total_actuals

        for target_region in region_ct_band_parameter._children:
            for target_ct_band in region_ct_band_parameter._children[
                target_region
            ]._children:
                actual = region_ct_band_parameter._children[
                    target_region
                ]._children[target_ct_band]
                comparisons.append(
                    (
                        f"{target_region}_{target_ct_band}",
                        (ct_band == target_ct_band)
                        & (region == target_region),
                        actual * region_ct_band_adjustment,
                    )
                )

        # Region - tenure type

        tenure_type = dataset.household.ons_tenure_type.values

        region_tenure_parameter = (
            self.calibration_parameters_at_instant.demographics.households.by_region_by_tenure_type
        )
        total_actuals = 0
        for target_region in region_tenure_parameter._children:
            regional_population = 0
            for target_tenure_type in region_tenure_parameter._children[
                target_region
            ]._children:
                total_actuals += region_tenure_parameter._children[
                    target_region
                ]._children[target_tenure_type]

        region_tenure_adjustment = uk_wide / total_actuals

        for target_region in region_tenure_parameter._children:
            regional_population = 0
            for target_tenure_type in region_tenure_parameter._children[
                target_region
            ]._children:
                actual_population = region_tenure_parameter._children[
                    target_region
                ]._children[target_tenure_type]
                comparisons.append(
                    (
                        f"{target_region}_{target_tenure_type}",
                        (tenure_type == target_tenure_type)
                        & (country == target_region),
                        actual_population * region_tenure_adjustment,
                    )
                )
                regional_population += actual_population

            comparisons += [
                (
                    f"households.{target_region}",
                    country == target_region,
                    regional_population * region_tenure_adjustment,
                )
            ]

        comparisons += [
            (
                "households.UNITED_KINGDOM",
                np.ones_like(region),
                uk_wide,
            )
        ]

        return comparisons
