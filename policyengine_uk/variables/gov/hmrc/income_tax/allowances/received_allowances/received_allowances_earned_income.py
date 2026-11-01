from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax_allocation import non_savings_deductions


class received_allowances_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Allowances deducted from non-savings income"
    documentation = (
        "The part of the allowances that Income Tax deducts from non-savings, "
        "non-dividend income, property income included. Trade loss relief "
        "against general income comes off that income first, inside "
        "net_income, so this is whatever the share in "
        "received_allowances_savings_income sets against that income beyond "
        "the relief."
    )
    unit = GBP
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007 s. 25",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
    )

    def formula(person, period, parameters):
        return non_savings_deductions(person, period).earned
