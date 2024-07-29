from policyengine_uk.model_api import *


class income_tax_pre_charges(Variable):
    value_type = float
    entity = Person
    label = "Income Tax before any tax charges"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )
    unit = GBP

    adds = [
        "earned_income_tax",
        "savings_income_tax",
        "dividend_income_tax",
    ]
