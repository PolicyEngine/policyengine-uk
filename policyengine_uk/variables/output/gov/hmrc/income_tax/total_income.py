from policyengine_uk.model_api import *


class total_income(Variable):
    value_type = float
    entity = Person
    label = "Taxable income after tax reliefs and before allowances"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 23",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
    )
    unit = GBP

    adds = [
        "employment_income",
        "private_pension_income",
        "social_security_income",
        "self_employment_income",
        "property_income",
        "savings_interest_income",
        "dividend_income",
        "miscellaneous_income",
    ]
