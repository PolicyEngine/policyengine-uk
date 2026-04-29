import numpy as np

from policyengine_uk.variables.contrib.policyengine.pre_budget_change_ons_household_income_decile import (
    pre_budget_change_ons_household_income_decile,
)
from policyengine_uk.variables.household.income.household_income_decile import (
    household_income_decile,
)


class FakeHousehold:
    def __init__(self, values, dataset=None):
        self.values = values
        self.simulation = type("FakeSimulation", (), {"dataset": dataset})()

    def __call__(self, variable, period):
        return np.array(self.values[variable])


def test_household_income_decile_caps_at_ten():
    household = FakeHousehold(
        {
            "equiv_hbai_household_net_income": np.arange(11, dtype=float),
            "household_count_people": np.ones(11),
            "household_weight": np.ones(11),
        }
    )

    result = household_income_decile.formula(household, 2025, None)

    assert np.all(result <= 10)
    assert result.max() == 10


def test_household_income_decile_keeps_negative_incomes_outside_deciles():
    household = FakeHousehold(
        {
            "equiv_hbai_household_net_income": np.array([-5, 0, 10], dtype=float),
            "household_count_people": np.ones(3),
            "household_weight": np.ones(3),
        }
    )

    result = household_income_decile.formula(household, 2025, None)

    assert result[0] == -1
    assert np.all(result[1:] >= 1)
    assert np.all(result[1:] <= 10)


def test_pre_budget_change_income_decile_domain_is_negative_or_one_to_ten():
    household = FakeHousehold(
        {
            "pre_budget_change_household_net_income": np.array(
                [-5, 16_000, 70_000], dtype=float
            ),
            "household_equivalisation_bhc": np.ones(3),
        }
    )

    result = pre_budget_change_ons_household_income_decile.formula(
        household, 2025, None
    )

    assert result.tolist() == [-1, 1, 10]
