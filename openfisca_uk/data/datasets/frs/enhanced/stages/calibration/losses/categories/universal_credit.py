from ..loss_category import LossCategory
from openfisca_uk.tools.simulation import Microsimulation
import tensorflow as tf
import numpy as np
from openfisca_core.parameters import ParameterNode, Parameter
from typing import Iterable, Tuple
from openfisca_uk.parameters import parameters

class UniversalCredit(LossCategory):
    name = "Universal Credit"
    category = "Programs"
    
    def initialise(self):
        self.uc = self.sim.calc("universal_credit", map_to="household", period=self.year).values

    def get_loss_subcomponents(self, household_weights: tf.Tensor) -> Iterable[Tuple]:
        yield "spending", tf.reduce_sum(household_weights * self.uc), 40e9