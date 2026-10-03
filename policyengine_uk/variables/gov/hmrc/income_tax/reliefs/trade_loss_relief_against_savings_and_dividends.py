from policyengine_uk.model_api import *


class trade_loss_relief_against_savings_and_dividends(Variable):
    value_type = float
    entity = Person
    label = "Trade loss relief deducted from savings and dividend income"
    documentation = (
        "The part of trade loss relief against general income left after "
        "non-savings income is used up; it joins the allowances applied to "
        "savings income and then to dividends. ITA 2007 s.25(2) deducts "
        "reliefs and allowances in the order giving the greatest reduction in "
        "liability, and from 2027-28 s.25(3A) puts income other than property, "
        "savings and dividends first. The model uses its fixed allowance order "
        "(non-savings income, property last, then savings, then dividends), "
        "which can overcharge where savings are taxed at 0%; that is model-wide "
        "and tracked in #2106."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 25",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
    )

    def formula(person, period, parameters):
        non_savings_income = (
            person("net_income_before_trade_loss_relief", period)
            - person("taxable_savings_interest_income", period)
            - person("taxable_dividend_income", period)
        )
        relief = person("trade_loss_relief_against_general_income", period)
        return max_(0, relief - max_(0, non_savings_income))
