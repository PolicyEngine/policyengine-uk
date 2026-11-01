from policyengine_uk.model_api import *


class non_savings_income_after_allowances(Variable):
    value_type = float
    entity = Person
    label = "Non-savings, non-dividend income for Income Tax after allowances"
    documentation = (
        "Net income (before the Gift Aid step of adjusted net income, which "
        "does not reduce the income charged to tax) less savings and dividend "
        "income and the reliefs and allowances set against non-savings "
        "income, floored at nil: the income below savings and dividends "
        "(ITA 2007 s. 16) once Steps 2 and 3 are done. ITA 2007 s. 25(2) "
        "decides how much of the reliefs and allowances comes off it, and "
        "from 2027-28 s. 25(3A) takes them off the rest of it before property "
        "income. property_income_tax and taxable_property_income_after_allowances "
        "both read it."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Income Tax Act 2007, s. 16",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/16",
        ),
        dict(
            title="Income Tax Act 2007, s. 25",
            href="https://www.legislation.gov.uk/ukpga/2007/3/section/25",
        ),
    ]
    unit = GBP

    def formula(person, period, parameters):
        return max_(
            0,
            # Not adjusted_net_income: it deducts the grossed-up Gift Aid
            # gift (ITA 2007 s. 58), which raises the rate limits instead
            # (s. 414(2)(b)) and is no deduction from taxable income.
            # net_income deducts all trade loss relief, so add back the part
            # set against savings and dividends (s. 25).
            person("net_income", period)
            + person("trade_loss_relief_against_savings_and_dividends", period)
            - person("taxable_savings_interest_income", period)
            - person("taxable_dividend_income", period)
            - person("received_allowances_earned_income", period),
        )
