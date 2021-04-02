from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class P_INEARNS(Variable):
    value_type = float
    entity = Person
    label = u"Gross earnings from employment"
    definition_period = WEEK

class P_GROSS4(Variable):
    value_type = float
    entity = Person
    label = u"Weight for adults"
    definition_period = YEAR

class B_GROSS4(Variable):
    value_type = float
    entity = BenUnit
    label = u"Weight for benefit units (families)"
    definition_period = YEAR

class H_GROSS4(Variable):
    value_type = float
    entity = Household
    label = u"Weight for households"
    definition_period = YEAR

class earnings(Variable):
    value_type = float
    entity = Person
    label = u"Gross earnings from employment"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("P_INEARNS", period, options=[ADD])


FRS_variables = [P_INEARNS, P_GROSS4, B_GROSS4, H_GROSS4]
input_variables = [earnings]


class from_FRS(Reform):
    def apply(self):
        for var in FRS_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)
