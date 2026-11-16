from policyengine_uk.model_api import *

# The exclusions that take earned income down to the non-savings income left
# after the allowances.
NON_SAVINGS_BASE = (
    "taxable_savings_interest_income",
    "taxable_dividend_income",
    "received_allowances_earned_income",
)


class earned_taxable_income(Variable):
    value_type = float
    entity = Person
    label = "Non-savings, non-dividend income for Income Tax"
    definition_period = YEAR
    reference = dict(
        title="Income Tax Act 2007, s. 10",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/10",
    )
    unit = GBP

    def formula(person, period, parameters):
        exclusion_list = parameters(
            period
        ).gov.hmrc.income_tax.earned_taxable_income_exclusions
        # net_income deducts all trade loss relief against general income.
        # Add back the part set against savings and dividends, which the
        # exclusions take off at their full amounts (ITA 2007 s. 25).
        income = person("net_income", period) + person(
            "trade_loss_relief_against_savings_and_dividends", period
        )
        exclusions = add(person, period, exclusion_list)
        earned = max_(0, income - exclusions)
        if all(variable in exclusion_list for variable in NON_SAVINGS_BASE):
            # Earned income is part of the non-savings income left after
            # the allowances, which the allocation computes without the
            # float32 rounding of the sum above.
            return min_(earned, person("non_savings_income_after_allowances", period))
        return earned
