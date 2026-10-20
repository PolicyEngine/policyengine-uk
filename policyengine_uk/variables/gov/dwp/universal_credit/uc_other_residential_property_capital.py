from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import less_sale_expenses


class uc_other_residential_property_capital(Variable):
    value_type = float
    entity = Household
    label = "Universal Credit net other residential property capital"
    documentation = (
        "Current assessment-year market value of other residential property, "
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
        market_value = max_(0, household("other_residential_property_value", period))
        debt = max_(0, household("other_residential_property_secured_debt", period))
        return max_(0, less_sale_expenses(market_value, p.sale_expenses.rate) - debt)
