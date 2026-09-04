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


def _simulation(rent: float, category: str):
    situation = {
        "people": {"person": {"age": {YEAR: 40}, "employment_income": {YEAR: 20_000}}},
        "benunits": {
            "benunit": {
                "members": ["person"],
                "LHA_category": {YEAR: category},
                "would_claim_uc": {YEAR: True},
            }
        },
        "households": {
            "household": {
                "members": ["person"],
                "brma": {YEAR: "CENTRAL_LONDON"},
                "tenure_type": {YEAR: "RENT_PRIVATELY"},
                "rent": {YEAR: rent},
            }
        },
    }
    return Simulation(situation=situation)


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
    """Central London category A is set by the percentile, not the maximum."""
    housing = _simulation(50_000, "A").calculate("uc_housing_costs_element", YEAR)[0]

    assert float(housing) < 1_439.97 * 12


def test_housing_benefit_keeps_the_weekly_maximum():
    """The Housing Benefit rate is unaffected by the monthly UC maximum."""
    rate = _simulation(50_000, "E").calculate("BRMA_LHA_rate", YEAR)[0]

    assert float(rate) / 52 == pytest.approx(704.22, abs=0.01)
