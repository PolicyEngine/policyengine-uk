"""Project the Carer's Allowance earnings limit from the national living wage.

Regulation 8(1) of the Social Security (Invalid Care Allowance) Regulations
1976 states the limit as a fixed sum, which each year's up-rating regulations
replace. From April 2025 the Government sets it at 16 times the hourly
national living wage, rounded up to the nearest pound, "from April 2025 and in
future years" (Explanatory Memorandum to SI 2025/352, paragraph 5.6): £196
from 16 x £12.21 = £195.36, and £204 from 16 x £12.71 = £203.36 (SI 2026/218).
Keep the legislated amounts and derive only later years, from the national
living wage in force on 30 April, as the April up-rating sets the limit.

Each projected year is the rule alone. A reform that lowers the national
living wage or the hours lowers the limit, and one that changes a single year
changes that year only. While the national living wage stays at or above its
April 2026 rate and the hours at or above 16, no projected year is below £204.

Run after general uprating and before fiscal-year conversion, on both the
main tree and its baseline copy. Reprocessing a reform then reads its changed
national living wage or hours. The exceptions edit the processed parameters, so they do not move the
limit: ``Scenario.apply`` on an already-built simulation, and a reform-dict
key naming a single day or month.
"""

import math
from typing import Any, Callable

from policyengine_core.parameters import Parameter, ParameterNode
from policyengine_core.parameters.parameter_at_instant import ParameterAtInstant
from policyengine_core.periods import instant

from policyengine_uk.parameters.gov.dwp.pension_credit.savings_credit.create_savings_credit_threshold import (
    last_projected_year,
)


def extend_after_last_stated(
    parameter: Parameter,
    last_year: int,
    derive: Callable[[str, Any], Any],
) -> None:
    """Add a value for each year after the parameter's last stated value.

    ``derive(sample, previous)`` gives the year's value from the other
    parameters at its 30 April ``sample``; ``previous`` is the value in force
    before it. Each value applies from 1 January, as uprating's do.
    """
    last = max(parameter.values_list, key=lambda entry: entry.instant_str)
    previous = last.value
    for year in range(int(last.instant_str[:4]) + 1, last_year + 1):
        previous = derive(f"{year}-04-30", previous)
        parameter.values_list.append(
            ParameterAtInstant(parameter.name, f"{year}-01-01", data=previous)
        )
    parameter.values_list.sort(key=lambda entry: entry.instant_str, reverse=True)
    parameter.mark_as_modified()


def national_living_wage_limit(hours: float, national_living_wage: float) -> float:
    """``hours`` at the national living wage, rounded up to the next pound.

    Rounding to six places first keeps an exact amount from rounding up when
    the float product sits just above it: 20 x (1,020 x 0.01) is
    204.00000000000003, which must give £204, not £205.
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
        return national_living_wage_limit(hours, national_living_wage)

    extend_after_last_stated(
        carers_allowance.earnings_limit, last_projected_year(parameters), derive
    )
    carers_allowance.clear_parent_cache()
    return parameters
