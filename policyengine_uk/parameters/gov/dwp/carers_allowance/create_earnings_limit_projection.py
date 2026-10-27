"""Project the Carer's Allowance earnings limit from the national living wage.

Regulation 8(1) of the Social Security (Invalid Care Allowance) Regulations
1976 states the limit as a fixed sum, which each year's up-rating regulations
replace. From April 2025 the Government sets it at 16 times the hourly
national living wage, rounded up to the nearest pound, "from April 2025 and in
future years" (Explanatory Memorandum to SI 2025/352, paragraph 5.6): £196
from 16 x £12.21 = £195.36, and £204 from 16 x £12.71 = £203.36 (SI 2026/218).
Keep the legislated amounts and derive only later years, from the national
living wage in force on 30 April, as the April up-rating sets the limit.

The limit has never been cut: each amount since 2015 is at least the one
before it. A year in which the national living wage would give a lower limit
keeps the limit in force before it.

Run after general uprating and before fiscal-year conversion, on both the
main tree and its baseline copy, as the Savings Credit threshold projection
is. Reprocessing a reform then reads its changed national living wage or
hours.
"""

import math

from policyengine_core.parameters import ParameterNode
from policyengine_core.periods import instant

from policyengine_uk.parameters.gov.dwp.pension_credit.savings_credit.create_savings_credit_threshold import (
    extend_after_last_stated,
    last_projected_year,
)


def national_living_wage_limit(hours: float, national_living_wage: float) -> float:
    """``hours`` at the national living wage, rounded up to the next pound.

    Rounding to six places first keeps an exact amount, such as 16 x £13.25 =
    £212, from rounding up when a float holds the wage just above £13.25.
    """
    return float(math.ceil(round(hours * national_living_wage, 6)))


def project_carers_allowance_earnings_limit(
    parameters: ParameterNode,
) -> ParameterNode:
    """Fill the years after the earnings limit's last stated value."""
    carers_allowance = parameters.gov.dwp.carers_allowance
    wage = parameters.gov.hmrc.minimum_wage.non_apprentice

    def derive(sample, previous):
        # The scale orders brackets by age, so its last amount is the adult
        # rate: the national living wage, as in
        # esa_exempt_work_higher_earnings_limit.
        national_living_wage = wage.get_at_instant(instant(sample)).amounts[-1]
        hours = carers_allowance.earnings_limit_national_living_wage_hours(sample)
        return max(previous, national_living_wage_limit(hours, national_living_wage))

    extend_after_last_stated(
        carers_allowance.earnings_limit, last_projected_year(parameters), derive
    )
    carers_allowance.clear_parent_cache()
    return parameters
