from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import Microsimulation
from typing import Iterable, List, Tuple
from openfisca_uk.parameters import parameters


class CountryLevelAggregates(LossCategory):
    weight = 1
    label = "Country-level aggregates"
    parameter_folder = parameters.calibration.households

    def get_loss_subcomponents(sim: Microsimulation, household_weights: tf.Tensor, year: int) -> Iterable[Tuple]:
        aggregates = CountryLevelAggregates.parameter_folder
        countries = aggregates.children
        hh_country = sim.calc("country")
        for country in countries:
            variables = countries[country].children
            for variable in variables:
                parameter = (
                    aggregates.children[country]
                    .children[variable]
                )
                in_country = hh_country == country
                values = sim.calc(variable, period=year).values
                entity = sim.simulation.tax_benefit_system.variables[
                    variable
                ].entity.key
                household_totals = sim.map_to(values, entity, "household")
                aggregate = tf.reduce_sum(
                    household_weights * in_country * household_totals
                )
                target = parameter(f"{year}-01-01")
                yield parameter.name + "." + str(year), aggregate, target
