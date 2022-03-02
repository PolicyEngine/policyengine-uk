import tensorflow as tf
from openfisca_uk.parameters import parameters
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
        ct_bands = HouseholdsByRegionByCouncilTaxBand.parameter_folder
        ct_band = sim.calc("council_tax_band")
        hh_region = sim.calc("region")
        for region in ct_bands.children:
            for band in ct_bands.children[region].children:
                parameter = ct_bands.children[region].children[band]
                parameter_name = parameter.name + "." + str(year)
                people_in_households = (
                    (hh_region == region) * (ct_band == band)
                ).values
                model_population = tf.reduce_sum(
                    household_weights * people_in_households
                )
                actual_population = parameter(f"{year}-01-01")
                if people_in_households.sum() > 0:
                    # If the FRS has no observations, skip the target.
                    yield parameter_name, model_population, actual_population
