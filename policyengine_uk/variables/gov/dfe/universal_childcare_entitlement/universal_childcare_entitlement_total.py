from policyengine_uk.model_api import *


class universal_childcare_entitlement_total(Variable):
    value_type = float
    entity = Household
    label = "Total universal childcare entitlement across UK"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(household, period, parameters):
        individual_entitlements = household.members("universal_childcare_entitlement", period)
        return household.sum(individual_entitlements)