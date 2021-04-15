from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class reported(Reform):
    def apply(self):
        self.neutralize_variable("benefits_modelling")
        self.neutralize_variable("tax_modelling")


class reported_tax(Reform):
    def apply(self):
        self.neutralize_variable("tax_modelling")


class reported_benefits(Reform):
    def apply(self):
        self.neutralize_variable("benefits_modelling")
