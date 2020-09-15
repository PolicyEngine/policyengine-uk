from openfisca_core.model_api import *
from openfisca_uk.entities import *

class basic_income(Variable):
    value_type = float
    entity = Person
    label = u'Amount of basic income received per week'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("adult", period) * 200

class family_basic_income(Variable):
    value_type = float
    entity = Family
    label = u'Amount of total basic income per week across the family'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family.sum(family.members('basic_income', period))

class family_total_income(Variable):
    value_type = float
    entity = Family
    label = u'Amount of total income per week across the family'
    definition_period = ETERNITY

    def formula(family, period, parameters):
        return family('family_earnings', period) + family('family_pension_income', period) + family('family_basic_income', period)

class simulation_3(Reform):
    def apply(self):
        for changed_var in [family_total_income]:
            self.update_variable(changed_var)
        for added_var in [basic_income, family_basic_income]:
            self.add_variable(added_var)