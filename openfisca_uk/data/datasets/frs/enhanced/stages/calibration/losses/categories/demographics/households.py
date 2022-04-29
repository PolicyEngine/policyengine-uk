from ...loss_category import LossCategory
import tensorflow as tf
from typing import Iterable, Tuple


class Households(LossCategory):
    name = "Households"
    category = "Demographics"

    def initialise(self):
        region_ct_band_parameter = (
            self.calibration_parameters.demographics.households.by_region_by_council_tax_band
        )

        self.comparisons = []

        ct_band = self.sim.calc("council_tax_band").values
        region = self.sim.calc("region").values

        # Region - CT band

        for target_region in region_ct_band_parameter._children:
            for target_ct_band in region_ct_band_parameter._children[
                target_region
            ]._children:
                self.comparisons.append(
                    (
                        f"{target_region}_{target_ct_band}",
                        (ct_band == target_ct_band)
                        & (region == target_region),
                        region_ct_band_parameter._children[
                            target_region
                        ]._children[target_ct_band],
                    )
                )

        # Region - tenure type

        tenure_type = self.sim.calc("ons_tenure_type").values

        region_tenure_parameter = (
            self.calibration_parameters.demographics.households.by_region_by_tenure_type
        )

        for target_region in region_tenure_parameter._children:
            for target_tenure_type in region_tenure_parameter._children[
                target_region
            ]._children:
                self.comparisons.append(
                    (
                        f"{target_region}_{target_tenure_type}",
                        (tenure_type == target_tenure_type)
                        & (region == target_region),
                        region_tenure_parameter._children[
                            target_region
                        ]._children[target_tenure_type],
                    )
                )

    def get_loss_subcomponents(
        self, household_weights: tf.Tensor
    ) -> Iterable[Tuple]:
        for name, values, actual in self.comparisons:
            yield (
                name,
                tf.reduce_sum(household_weights * values),
                actual,
            )

    def get_metric_names(self) -> Iterable[str]:
        return [x[0] for x in self.comparisons]
