import numpy as np
import pytest

from policyengine_uk import CountryTaxBenefitSystem


class FakeHousehold:
    def __init__(self, incomes, sizes, weights):
        self.values = {
            "equiv_hbai_household_net_income_ahc": np.array(incomes, dtype=float),
            "household_count_people": np.array(sizes, dtype=float),
            "household_weight": np.array(weights, dtype=float),
        }
        self.simulation = type("FakeSimulation", (), {"dataset": None})()

    def __call__(self, variable, period):
        return self.values[variable]


@pytest.fixture(scope="module")
def tax_benefit_system():
    return CountryTaxBenefitSystem()


def formula(tax_benefit_system):
    variable = tax_benefit_system.variables.get("household_income_decile_ahc")
    assert variable is not None, "The AHC income decile must be registered"
    return variable.get_formula("2025-01-01")


def test_household_income_decile_ahc_is_registered(tax_benefit_system):
    variable = tax_benefit_system.variables.get("household_income_decile_ahc")
    assert variable is not None, "The AHC income decile must be registered"
    assert variable.entity.key == "household"
    assert variable.definition_period == "year"
    assert variable.value_type is int


def test_household_income_decile_ahc_weights_people_and_survey_weights(
    tax_benefit_system,
):
    # Person masses are 2, 1, 2. In income order the cumulative shares are
    # one fifth, three fifths, and one: deciles 2, 6, and 10.
    household = FakeHousehold([3000, 1000, 2000], [1, 1, 2], [2, 1, 1])
    result = formula(tax_benefit_system)(household, 2025, None)
    np.testing.assert_array_equal(result, [10, 2, 6])


def test_household_income_decile_ahc_floors_only_ranking_and_groups_zero_ties(
    tax_benefit_system,
):
    # Three tenths of people have nonpositive AHC income. For ranking they
    # share the top of the zero group, decile 3, while their incomes stay negative.
    incomes = [-500, -1, 0, 1, 2, 3, 4, 5, 6, 7]
    household = FakeHousehold(incomes, np.ones(10), np.ones(10))
    result = formula(tax_benefit_system)(household, 2025, None)
    np.testing.assert_array_equal(result, [3, 3, 3, 4, 5, 6, 7, 8, 9, 10])
    np.testing.assert_array_equal(
        household.values["equiv_hbai_household_net_income_ahc"], incomes
    )


def test_household_income_decile_ahc_positive_ties_share_top_rank(tax_benefit_system):
    # Income 1000 represents two tenths of people; the 2000 tie adds four
    # tenths. Both tied households therefore receive decile 6.
    household = FakeHousehold([2000, 1000, 2000, 3000], [1, 1, 1, 1], [1, 2, 3, 4])
    result = formula(tax_benefit_system)(household, 2025, None)
    np.testing.assert_array_equal(result, [6, 2, 6, 10])


def test_household_income_decile_ahc_caps_top_rank_at_ten(tax_benefit_system):
    household = FakeHousehold(np.arange(11), np.ones(11), np.ones(11))
    result = formula(tax_benefit_system)(household, 2025, None)
    np.testing.assert_array_equal(result, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10])
