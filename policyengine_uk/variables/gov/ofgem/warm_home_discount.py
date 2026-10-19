from policyengine_uk.model_api import *


class warm_home_discount(Variable):
    value_type = float
    entity = Household
    label = "Warm Home Discount"
    documentation = (
        "Rebate an electricity supplier gives the household under the Warm "
        "Home Discount scheme in England and Wales, in the year containing "
        "the winter it is paid for. A household qualifies if any member "
        "receives a qualifying means-tested benefit; the rebate is paid "
        "without a claim. Suppliers fund the rebate from their customers' "
        "bills, so it is not government spending, and it is not included in "
        "household_benefits or household_net_income. The model doesn't check "
        "the supplier, account-holder or property conditions, and doesn't "
        "calculate the separate Scottish scheme."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2026/389/contents/made",
        "https://www.gov.uk/the-warm-home-discount-scheme",
    )

    def formula(household, period, parameters):
        p = parameters(period).gov.ofgem.warm_home_discount
        country = household("country", period)
        countries = country.possible_values
        in_scheme_area = (country == countries.ENGLAND) | (country == countries.WALES)
        benefits = p.qualifying_benefits
        if len(benefits) == 0:
            return household.empty_array()
        receives_benefit = add(household, period, benefits) > 0
        return in_scheme_area * receives_benefit * p.amount
