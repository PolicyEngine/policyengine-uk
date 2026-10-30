from policyengine_uk.model_api import *


class non_cash_isa_cash_interest(Variable):
    value_type = float
    entity = Person
    label = "Of which ISA interest: cash held in non-cash ISAs"
    documentation = "Annual interest or alternative-finance returns on cash held in stocks-and-shares or innovative-finance ISAs. This is a component of total ISA interest, not an additional market-income amount; supplied totals must include it. The final manager charge starts in fiscal 2027-28."
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    # Same per-person index as savings_interest_income (#1862): household
    # weights already grow by population.
    uprating = (
        "gov.economic_assumptions.indices.ons.per_capita.household_interest_income"
    )
    reference = "https://www.legislation.gov.uk/uksi/2026/1018/regulation/15/made"
