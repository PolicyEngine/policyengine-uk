from policyengine_uk.model_api import *


class unit_and_investment_trusts(Variable):
    label = "unit and investment trusts"
    documentation = (
        "Value of the household's holdings of unit trusts and investment trusts "
        "outside ISAs. The Wealth and Assets Survey asks about both in one "
        "question, so the Enhanced FRS cannot separate them. Part of "
        "corporate_wealth, so the two must never be summed. Unit trusts are "
        "valued for the means tests at the price the manager pays on "
        "withdrawal, with no deduction for expenses of sale (Advice for "
        "Decision Making H1673-H1674)."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    quantity_type = STOCK
    default_value = 0
