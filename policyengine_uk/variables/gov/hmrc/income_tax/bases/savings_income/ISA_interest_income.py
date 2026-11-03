from policyengine_uk.model_api import *
from policyengine_uk.data.isa_income import isa_interest_income_default


class individual_savings_account_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Amount received in interest from Individual Savings Accounts"
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    documentation = (
        "ISA interest, additional to ordinary savings_interest_income. The "
        "non-cash ISA cash-interest input is an of-which detail: it supplies "
        "this total only when no total is provided."
    )
    reference = dict(
        title="Income Tax (Trading and Other Income) Act 2005, Part 6, Chapter 3",
        href="https://www.legislation.gov.uk/ukpga/2005/5/part/6/chapter/3",
    )

    def formula(person, period, parameters):
        # Detail defaults and origin-aware uprating share one formula mode:
        # Core does not allow a variable to combine formula and uprating.
        return isa_interest_income_default(person.simulation, period)
