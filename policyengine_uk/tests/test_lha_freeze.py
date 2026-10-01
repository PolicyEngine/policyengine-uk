"""Regression tests for the LHA freeze parameter."""

import pytest

from policyengine_uk import Simulation


YEAR = 2026

SITUATION = {
    "people": {
        "person": {
            "age": {YEAR: 30},
            "employment_income": {YEAR: 0},
        }
    },
    "benunits": {
        "benunit": {
            "members": ["person"],
            "benunit_rent": {YEAR: 10_000},
            "LHA_eligible": {YEAR: True},
            "housing_benefit_applicable_amount": {YEAR: 11_000},
            "housing_benefit_applicable_income": {YEAR: 11_000},
            "housing_benefit_non_dep_deductions": {YEAR: 0},
        }
    },
    "households": {
        "household": {
            "members": ["person"],
            "region": {YEAR: "LONDON"},
        }
    },
}


def test_lha_freeze_changes_lha_rate_and_housing_benefit_entitlement():
    frozen = Simulation(
        situation=SITUATION,
        reform={"gov.dwp.LHA.freeze": {"2026": True}},
    )
    unfrozen = Simulation(
        situation=SITUATION,
        reform={"gov.dwp.LHA.freeze": {"2026": False}},
    )

    frozen_rate = frozen.calculate("BRMA_LHA_rate", YEAR)[0]
    unfrozen_rate = unfrozen.calculate("BRMA_LHA_rate", YEAR)[0]
    frozen_entitlement = frozen.calculate("housing_benefit_entitlement", YEAR)[0]
    unfrozen_entitlement = unfrozen.calculate("housing_benefit_entitlement", YEAR)[0]

    assert unfrozen_rate > frozen_rate
    assert unfrozen_entitlement > frozen_entitlement


def _lha_rate(year: int, brma: str = "INNER_EAST_LONDON") -> float:
    """Annual BRMA LHA rate for a single adult renting privately."""
    situation = {
        "people": {"person": {"age": {year: 35}}},
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "brma": {year: brma},
                "tenure_type": {year: "RENT_PRIVATELY"},
                "rent": {year: 20_000},
            }
        },
    }
    return float(Simulation(situation=situation).calculate("BRMA_LHA_rate", year)[0])


def test_frozen_rates_hold_at_the_last_unfrozen_year():
    """Frozen LHA rates are held in cash terms, not re-based each year.

    The published rates for 2025/26 and 2026/27 are identical to 2024/25:
    SI 2025/5 and SI 2026/5 exclude the September 2024 and 2025 evidence and
    carry the April 2024 determination forward.
    """
    reset_2024 = _lha_rate(2024)

    for frozen_year in (2025, 2026, 2027):
        assert _lha_rate(frozen_year) == reset_2024, (
            f"{frozen_year} should hold the April 2024 rate"
        )


def test_the_2020_freeze_holds_at_the_2020_reset():
    """April 2020 was itself a reset, with the freeze running from April 2021."""
    reset_2020 = _lha_rate(2020)

    for frozen_year in (2021, 2022, 2023):
        assert _lha_rate(frozen_year) == reset_2020, (
            f"{frozen_year} should hold the April 2020 rate"
        )


def test_the_2024_reset_raises_rates_above_the_2020_freeze():
    assert _lha_rate(2024) > _lha_rate(2023)


def _weekly_rate(year: int, brma: str, category: str, reform=None) -> float:
    situation = {
        "people": {"person": {"age": {year: 35}}},
        "benunits": {
            "benunit": {"members": ["person"], "LHA_category": {year: category}}
        },
        "households": {
            "household": {
                "members": ["person"],
                "brma": {year: brma},
                "tenure_type": {year: "RENT_PRIVATELY"},
                "rent": {year: 100_000},
            }
        },
    }
    annual = Simulation(situation=situation, reform=reform).calculate(
        "BRMA_LHA_rate", year
    )[0]
    return float(annual) / 52


def test_a_reset_year_is_not_treated_as_a_hold():
    """2020 was a reset, so its rate comes from 2020 rents, not earlier ones.

    Asserting only that the frozen years equal 2020 would still pass if 2020
    were itself wrongly marked frozen, because every compared year would then
    move together. Comparing against that mutation is what catches it.
    """
    reset = _weekly_rate(2020, "MAIDSTONE", "C")
    held_instead = _weekly_rate(
        2020, "MAIDSTONE", "C", reform={"gov.dwp.LHA.freeze": {"2020": True}}
    )

    assert reset == pytest.approx(187.91, abs=0.01)
    assert held_instead != pytest.approx(reset, abs=0.01)


def test_frozen_years_hold_the_reset_level_for_an_uncapped_area():
    """The national maximum never binds in Maidstone, so this isolates the
    freeze from the cap."""
    reset = _weekly_rate(2020, "MAIDSTONE", "C")

    for frozen_year in (2021, 2022, 2023):
        assert _weekly_rate(frozen_year, "MAIDSTONE", "C") == pytest.approx(
            reset, abs=0.01
        )
