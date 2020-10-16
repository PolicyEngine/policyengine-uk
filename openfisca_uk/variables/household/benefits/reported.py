from openfisca_core.model_api import *
from openfisca_uk.entities import *


class household_WFA_reported(Variable):
    value_type = float
    entity = Household
    label = u"Reported amount of Winter Fuel Allowance per week"
    definition_period = ETERNITY

    def formula(household, period, parameters):
        return household.sum(household.members("winter_fuel_allowance_reported", period))
