from policyengine_uk.model_api import *


class household_uc_reported_financial_capital(Variable):
    value_type = float
    entity = Household
    label = "Household financial capital observed for benefit units"
    documentation = (
        "Sum of nonnegative benunit_reported_capital observations, counted "
        "once per benefit unit. Only these financial observations reduce the "
        "household financial proxy. A complete uc_reported_capital override "
        "has an unknown financial/property decomposition and is never "
        "subtracted from that financial pool."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        person = household.members
        financial_capital = person.benunit("benunit_reported_capital", period)
        return household.sum(
            max_(0, financial_capital) * person("is_benunit_head", period)
        )
