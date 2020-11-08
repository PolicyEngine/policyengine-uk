from openfisca_core.model_api import *
from openfisca_uk.entities import *


class benefits_as_reported(Reform):
    def apply(self):
        self.neutralize_variable("benefit_modelling")
