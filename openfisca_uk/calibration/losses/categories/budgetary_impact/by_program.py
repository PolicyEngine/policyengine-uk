from openfisca_uk.calibration.losses.loss_category import LossCategory
import tensorflow as tf
from openfisca_uk import Microsimulation
from typing import Iterable, List, Tuple
from openfisca_uk import parameters


class BudgetaryImpactByProgram(LossCategory):
    label = "Budgetary impact by program"
    parameter_folder = parameters.calibration.budgetary_impact.by_program
    weight = 1 / 3

    def get_loss_subcomponents(
        sim: Microsimulation, household_weights: tf.Tensor, year: int
    ) -> Iterable[Tuple]:
        aggregates = BudgetaryImpactByProgram.parameter_folder
        variables = aggregates.children
        for variable in variables:
            values = sim.calc(variable, period=year, map_to="household").values
            # Calculate aggregate error
            agg = tf.reduce_sum(household_weights * values)
            parameter = aggregates.children[variable]
            actual = parameter(f"{year}-01-01")
            yield parameter.name + "." + str(year), agg, actual
