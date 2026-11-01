from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax_allocation import allocate_deductions


class received_allowances_dividend_income(Variable):
    value_type = float
    entity = Person
    label = "Allowances and reliefs deducted from dividend income"
    documentation = (
        "The part of the allowances and trade loss relief against general "
        "income that Income Tax deducts from dividend income, in the share "
        "that gives the least tax (ITA 2007 s. 25(2) and, from 2027-28, "
        "s. 25(3A)). See received_allowances_savings_income."
    )
    unit = GBP
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 25",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
    )

    def formula(person, period, parameters):
        return allocate_deductions(person, period, parameters).dividends
