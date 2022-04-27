from ...loss_category import LossCategory
from openfisca_uk.tools.simulation import Microsimulation
import tensorflow as tf
import numpy as np
from openfisca_core.parameters import ParameterNode, Parameter
from typing import Iterable, Tuple
from openfisca_uk.parameters import parameters

class CountryLevelProgram(LossCategory):
    category = "Programs"
    variable: str
    
    def initialise(self):
        values = self.sim.calc(self.variable, map_to="household", period=self.year).values
        countries = self.sim.calc("country").values
        self.values = []
        self.targets = []
        self.names = []

        parameter = self.calibration_parameters.programs._children[self.variable]

        if "UNITED_KINGDOM" in parameter.budgetary_impact._children:
            self.values += [values]
            self.targets += [parameter.budgetary_impact._children["UK"]]
            self.names += ["budgetary_impact_UNITED_KINGDOM"]
        if "GREAT_BRITAIN" in parameter.budgetary_impact._children:
            self.values += [values * (countries != "NORTHERN_IRELAND")]
            self.targets += [parameter.budgetary_impact._children["GREAT_BRITAIN"]]
            self.names += ["budgetary_impact_GREAT_BRITAIN"]
        for single_country in ("ENGLAND", "WALES", "SCOTLAND", "NORTHERN_IRELAND"):
            if single_country in parameter.budgetary_impact._children:
                self.values += [values * (countries == single_country)]
                self.targets += [parameter.budgetary_impact._children[single_country]]
                self.names += [f"budgetary_impact_{single_country}"]

    def get_loss_subcomponents(self, household_weights: tf.Tensor) -> Iterable[Tuple]:
        for name, values, target in zip(self.names, self.values, self.targets):
            yield (
                name,
                tf.reduce_sum(household_weights * values),
                target,
            )