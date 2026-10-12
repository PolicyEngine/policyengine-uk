"""The relative poverty flags take their median over individuals (HBAI's basis), not households.

Regression tests for https://github.com/PolicyEngine/policyengine-uk/issues/1865.
"""

import numpy as np

from policyengine_uk.variables.household.income.in_relative_poverty_ahc import (
    in_relative_poverty_ahc,
)
from policyengine_uk.variables.household.income.in_relative_poverty_bhc import (
    in_relative_poverty_bhc,
)


class FakeHousehold:
    def __init__(self, values):
        self.values = values

    def __call__(self, variable, period):
        return np.array(self.values[variable])


# Three households, one survey weight each. The single adult on 20,000 is the
# median household (median over households = 20,000, line = 12,000, nobody
# flagged), but the family of four on 30,000 holds most of the people, so the
# median over individuals is 30,000 and the line 18,000, which flags the
# household on 15,000.
INCOMES = np.array([15_000.0, 20_000.0, 30_000.0])
PEOPLE = np.array([1, 1, 4])
WEIGHTS = np.array([1.0, 1.0, 1.0])
EXPECTED_PERSON_BASIS = [True, False, False]


def test_bhc_flag_uses_the_median_over_individuals():
    household = FakeHousehold(
        {
            "equiv_hbai_household_net_income": INCOMES,
            "household_count_people": PEOPLE,
            "household_weight": WEIGHTS,
        }
    )

    result = in_relative_poverty_bhc.formula(household, 2025, None)

    assert list(result) == EXPECTED_PERSON_BASIS


def test_ahc_flag_uses_the_median_over_individuals():
    household = FakeHousehold(
        {
            "equiv_hbai_household_net_income_ahc": INCOMES,
            "household_count_people": PEOPLE,
            "household_weight": WEIGHTS,
        }
    )

    result = in_relative_poverty_ahc.formula(household, 2025, None)

    assert list(result) == EXPECTED_PERSON_BASIS


def test_household_size_alone_does_not_move_the_line_when_everyone_is_equal():
    # Same fixture with every household at one person: the median is the
    # middle household and only the household below 60% of it is flagged.
    household = FakeHousehold(
        {
            "equiv_hbai_household_net_income": np.array([10_000.0, 20_000.0, 30_000.0]),
            "household_count_people": np.ones(3),
            "household_weight": np.ones(3),
        }
    )

    result = in_relative_poverty_bhc.formula(household, 2025, None)

    assert list(result) == [True, False, False]
