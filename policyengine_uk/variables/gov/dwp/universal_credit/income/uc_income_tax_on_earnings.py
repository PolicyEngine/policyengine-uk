from policyengine_uk.model_api import *
from policyengine_uk.utils.uc_income_tax import uc_income_tax_on_earnings_slice


class uc_income_tax_on_earnings(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit deduction for income tax on the person's earnings"
    documentation = (
        "Income tax the person pays in respect of their own employment and "
        "self-employment, which Universal Credit deducts from their earned "
        "income. Tax on pensions, State Pension, property, savings and "
        "dividends is not deducted, nor is the High Income Child Benefit "
        "Charge or the pension annual allowance charge."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 55(5)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/55",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 57(2), step 3",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/57",
        ),
        dict(
            title="Income Tax Act 2007 s. 16",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/16",
        ),
    ]

    def formula(person, period, parameters):
        return uc_income_tax_on_earnings_slice(person, period, parameters)
