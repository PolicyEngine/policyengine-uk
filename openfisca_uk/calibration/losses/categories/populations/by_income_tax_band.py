import numpy as np
from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import parameters


class PopulationsByIncomeTaxBand(LossCategory):
    label = "Income tax payers by income"
    parameter_folder = parameters.calibration.populations.by_income_tax_band
    weight = 1 / 30

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        tax_band = sim.calc("tax_band", period=year).values
        pays_basic_rate = (
            (tax_band == "BASIC")
            | (tax_band == "INTERMEDIATE")
            | (tax_band == "STARTER")
        )
        pays_higher_rate = tax_band == "HIGHER"
        pays_add_rate = tax_band == "ADDITIONAL"

        basic_rate_payers = sim.map_to(pays_basic_rate, "person", "household")
        higher_rate_payers = sim.map_to(
            pays_higher_rate, "person", "household"
        )
        add_rate_payers = sim.map_to(pays_add_rate, "person", "household")
        taxpayers = PopulationsByIncomeTaxBand.parameter_folder

        for value, target in zip(
            [
                basic_rate_payers,
                higher_rate_payers,
                add_rate_payers,
            ],
            [
                taxpayers.BASIC,
                taxpayers.HIGHER,
                taxpayers.ADDITIONAL,
            ],
        ):
            population = tf.reduce_sum(household_weights * value)
            yield target.name + "." + str(year), population, target(
                f"{year}-01-01"
            )
