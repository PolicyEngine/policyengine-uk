from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax_allocation import non_savings_deductions


class trade_loss_relief_against_savings_and_dividends(Variable):
    value_type = float
    entity = Person
    label = "Trade loss relief deducted from savings and dividend income"
    documentation = (
        "The part of trade loss relief against general income that Income Tax "
        "deducts from savings and dividend income. ITA 2007 s. 25(2) deducts "
        "reliefs and allowances in the way that gives the least tax, and from "
        "2027-28 s. 25(3A) deducts them from income other than property, "
        "savings and dividend income first; received_allowances_savings_income "
        "and received_allowances_dividend_income hold that share. The relief "
        "comes off non-savings income first, as far as the share sets anything "
        "against that income, and this is the rest. net_income deducts the "
        "whole relief, so the non-savings bases add this back."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 25",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
    )

    def formula(person, period, parameters):
        return non_savings_deductions(
            person, period
        ).relief_against_savings_and_dividends
