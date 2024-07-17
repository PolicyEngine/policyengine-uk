from policyengine_uk.model_api import *


class income_tax(Variable):
    value_type = float
    entity = Person
    label = "Income Tax"
    documentation = "Total Income Tax liability"
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )
    category = TAX
    adds = [
        "earned_income_tax",
        "savings_income_tax",
        "dividend_income_tax",
        "CB_HITC",
    ]
    subtracts = [
        "capped_mcad",
    ]
