from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class household_net_income(Variable):
    value_type = float
    entity = Household
    label = u'Household net income, before housing costs'
    definition_period = YEAR

    def formula(household, period, parameters):
        return max_(0, aggr(household, period, ["net_income"]))

class household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = u'Household net income, after housing costs'
    definition_period = YEAR

    def formula(household, period, parameters):
        return max_(0, aggr(household, period, ["net_income"]) - household("housing_costs", period, options=[MATCH]))

class equiv_household_net_income(Variable):
    value_type = float
    entity = Household
    label = u'Equivalised household net income, before housing costs'
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("household_net_income", period) / household("household_equivalisation_bhc", period)

class equiv_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = u'Equivalised household net income, after housing costs'
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("household_net_income_ahc", period) / household("household_equivalisation_ahc", period)