from policyengine_uk.model_api import *


class uc_non_residential_property_capital(Variable):
    value_type = float
    entity = Household
    label = "Universal Credit net non-residential property capital"
    documentation = (
        "Current assessment-year market value of non-residential property, "
        "less the regulation 49 sale-expense deduction, then secured debt, "
        "floored at zero. Assumes sale expenses and no Schedule 10 disregard "
        "within this broad property class. Property-specific secured debt "
        "defaults to zero because reliable survey debt flags are unavailable."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/49/1"

    def formula(household, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.means_test.capital
        market_value = max_(0, household("non_residential_property_value", period))
        debt = max_(0, household("non_residential_property_secured_debt", period))
        return max_(0, market_value * (1 - p.sale_expenses.rate) - debt)
