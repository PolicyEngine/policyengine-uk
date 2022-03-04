import numpy as np
import tensorflow as tf
from openfisca_uk.parameters import parameters
from openfisca_uk.calibration.losses.loss_category import LossCategory


class RegionalPopulations(LossCategory):
    weight = 1
    label = "Regional populations"
    parameter_folder = parameters.calibration.regional_populations

    def get_loss_subcomponents(
        sim,
        household_weights,
        year,
    ):
        household_region = sim.calc("region").values
        household_population = sim.calc("people", map_to="household").values
        regions = RegionalPopulations.parameter_folder.children
        for region in regions:
            in_region = household_region == region
            people_in_region = household_population * in_region
            population = tf.reduce_sum(people_in_region * household_weights)
            target = regions[region](f"{year}-01-01")
            yield regions[region].name + "." + str(year), population, target
