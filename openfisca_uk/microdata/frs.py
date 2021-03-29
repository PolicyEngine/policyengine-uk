from numpy.core.fromnumeric import var
from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class INEARNS(Variable):
    value_type = float
    entity = Person
    label = u"Gross earnings from employment"
    definition_period = WEEK

class earnings(Variable):
    value_type = float
    entity = Person
    label = u"Gross earnings from employment"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("INEARNS", period, options=[ADD])

FRS_variables = [INEARNS]
input_variables = [earnings]

class from_FRS(Reform):
    def apply_reform(self):
        for var in FRS_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)