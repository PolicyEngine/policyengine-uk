import tensorflow as tf
from openfisca_uk.parameters import parameters
from openfisca_uk.calibration.losses.loss_category import LossCategory


class CouncilTaxBandHouseholds(LossCategory):
    weight = 1e3
    label = "Council Tax Band Households"
    parameter_folder = parameters.calibration.council_tax_band_counts

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        ct_bands = CouncilTaxBandHouseholds.parameter_folder
        ct_band = sim.calc("council_tax_band")
        hh_country = sim.calc("country")
        for country in ct_bands.children:
            for band in ct_bands.children[country].children:
                parameter = ct_bands.children[country].children[band]
                parameter_name = parameter.name + "." + str(year)
                model_population = tf.reduce_sum(
                    (hh_country == country)
                    * (ct_band == band)
                    * household_weights
                )
                actual_population = parameter(f"{year}-01-01")
                yield parameter_name, model_population, actual_population
