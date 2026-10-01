"""Universal Credit applies its own monthly national maximum LHA.

The monthly figures in Schedule 1 to the Rent Officers (Universal Credit
Functions) Order 2013 are set independently of the weekly Housing Benefit
maxima, and are slightly higher. Annualising the weekly figure would impose a
ceiling below the statutory one.
"""

import pytest

from policyengine_uk import Simulation

YEAR = 2024

# SI 2024/11, article 4(2)(b). Category A is omitted because central
# London's shared-accommodation percentile sits well below its maximum, so
# the ceiling never binds there; it is covered separately below.
BINDING_MONTHLY_MAXIMA = {
    "B": 1_439.97,
    "C": 1_793.98,
    "D": 2_160.02,
    "E": 3_060.00,
}


def _situation(rent: float, category: str, year: int = YEAR):
    return {
        "people": {"person": {"age": {year: 40}, "employment_income": {year: 20_000}}},
        "benunits": {
            "benunit": {
                "members": ["person"],
                "LHA_category": {year: category},
                "would_claim_uc": {year: True},
            }
        },
        "households": {
            "household": {
                "members": ["person"],
                "brma": {year: "CENTRAL_LONDON"},
                "tenure_type": {year: "RENT_PRIVATELY"},
                "rent": {year: rent},
            }
        },
    }


def _simulation(rent: float, category: str, year: int = YEAR, reform=None):
    return Simulation(situation=_situation(rent, category, year), reform=reform)


@pytest.mark.parametrize("category,monthly", BINDING_MONTHLY_MAXIMA.items())
def test_uc_ceiling_is_the_statutory_monthly_maximum(category, monthly):
    """Rent above the ceiling is covered only up to twelve monthly maxima."""
    ceiling = monthly * 12
    housing = _simulation(ceiling + 10_000, category).calculate(
        "uc_housing_costs_element", YEAR
    )[0]

    assert float(housing) == pytest.approx(ceiling, abs=0.01)


def test_uc_covers_rent_below_the_ceiling():
    """Rent under the ceiling but over the annualised weekly cap is covered.

    Category E's weekly maximum annualises to £36,619.44, below the statutory
    monthly ceiling of £36,720, so this rent is the case that distinguishes
    the two.
    """
    rent = 36_670
    housing = _simulation(rent, "E").calculate("uc_housing_costs_element", YEAR)[0]

    assert float(housing) == pytest.approx(rent, abs=0.01)


def test_a_rate_below_the_ceiling_is_not_raised_to_it():
    """Central London category A is set by the percentile, not the maximum.

    Asserting only that the result is under the ceiling would also pass if it
    were zero or wrongly low, so this compares against the same case with the
    monthly maximum lifted out of the way.
    """
    housing = _simulation(50_000, "A").calculate("uc_housing_costs_element", YEAR)[0]
    unlimited = _simulation(
        50_000,
        "A",
        reform={"gov.dwp.LHA.maximum_monthly.A": {str(YEAR): 100_000}},
    ).calculate("uc_housing_costs_element", YEAR)[0]

    assert float(housing) == pytest.approx(float(unlimited), abs=0.01)
    assert 0 < float(housing) < 1_439.97 * 12


def test_housing_benefit_keeps_the_weekly_maximum():
    """The Housing Benefit rate is unaffected by the monthly UC maximum."""
    rate = _simulation(50_000, "E").calculate("BRMA_LHA_rate", YEAR)[0]

    assert float(rate) / 52 == pytest.approx(704.22, abs=0.01)


def test_the_monthly_maximum_does_not_apply_before_it_existed():
    """The monthly series starts in April 2020.

    Parameters are backdated to 2015 on load, so without an explicit gate the
    2020 maximum would apply to earlier years, where it is far above the
    figures actually in force. Before the series starts, Universal Credit
    falls back to the weekly Housing Benefit rate.
    """
    simulation = _simulation(50_000, "E", year=2019)
    housing = simulation.calculate("uc_housing_costs_element", 2019)[0]
    weekly_rate = simulation.calculate("BRMA_LHA_rate", 2019)[0]

    assert float(housing) == pytest.approx(float(weekly_rate), abs=0.01)
    assert float(housing) < 2_579.98 * 12


def test_the_monthly_maximum_applies_from_2020():
    """The 2019/2020 boundary: 2020 uses the monthly maximum, 2019 does not."""
    housing_2020 = _simulation(50_000, "E", year=2020).calculate(
        "uc_housing_costs_element", 2020
    )[0]

    assert float(housing_2020) == pytest.approx(2_579.98 * 12, abs=0.01)
