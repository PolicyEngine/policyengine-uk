from policyengine_uk.model_api import *


class household_uc_reported_capital(Variable):
    value_type = float
    entity = Household
    label = "Household Universal Credit capital explicitly reported by benunits"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        person = household.members
        reported_capital = person.benunit("uc_reported_capital", period)
        has_reported_capital = reported_capital >= 0
        is_benunit_head = person("is_benunit_head", period)
        return household.sum(
            reported_capital * has_reported_capital * is_benunit_head
        )
