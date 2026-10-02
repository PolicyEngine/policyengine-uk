from policyengine_uk.model_api import *


class trade_loss_relief_against_savings_and_dividends(Variable):
    value_type = float
    entity = Person
    label = "Trade loss relief deducted from savings and dividend income"
    documentation = (
        "The part of trade loss relief against general income left after "
        "non-savings income is used up; it joins the allowances applied to "
        "savings income and then to dividends. From 2027-28 ITA 2007 s.25(3A) "
        "requires reliefs to come off income other than property, savings and "
        "dividend income first. Before then s.25(2) asks for the order giving "
        "the greatest reduction in liability, which the model takes to be the "
        "same order, as it does for the Personal Allowance: non-savings income "
        "(property last), then savings, then dividends."
    )
    definition_period = YEAR
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 25",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
    )

    def formula(person, period, parameters):
        components = parameters(
            period
        ).gov.hmrc.income_tax.adjusted_net_income_components
        non_savings_income = (
            add(person, period, components)
            - person("taxable_savings_interest_income", period)
            - person("taxable_dividend_income", period)
        )
        relief = person("trade_loss_relief_against_general_income", period)
        return max_(0, relief - max_(0, non_savings_income))
