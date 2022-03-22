import tensorflow as tf
from openfisca_uk import parameters
from openfisca_uk.calibration.losses.loss_category import LossCategory


class HouseholdsByRegionByCouncilTaxBand(LossCategory):
    label = "Households by region and council tax band"
    parameter_folder = (
        parameters.calibration.households.by_region_by_council_tax_band
    )

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        total_households = parameters.calibration.households.in_total(
            f"{year}-01-01"
        )
        total_tenure_metrics = sum(
            [
                parameter(f"{year}-01-01")
                for parameter in HouseholdsByRegionByCouncilTaxBand.get_metrics()
            ]
        )
        adjustment = total_households / total_tenure_metrics
        ct_bands = HouseholdsByRegionByCouncilTaxBand.parameter_folder
        ct_band = sim.calc("council_tax_band")
        hh_region = sim.calc("region")
        for region in ct_bands.children:
            for band in ct_bands.children[region].children:
                parameter = ct_bands.children[region].children[band]
                parameter_name = parameter.name + "." + str(year)
                household_in_condition = (
                    (hh_region == region) * (ct_band == band)
                ).values
                model_population = tf.reduce_sum(
                    household_weights * household_in_condition
                )
                actual_population = parameter(f"{year}-01-01") * adjustment
                if household_in_condition.sum() > 0:
                    # If the FRS has no observations, skip the target.
                    yield parameter_name, model_population, actual_population
