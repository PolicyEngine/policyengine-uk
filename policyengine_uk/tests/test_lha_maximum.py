"""The national maximum LHA caps the BRMA percentile.

Published LHA rates are the lower of the Broad Rental Market Area percentile
and the national maximum for the category (Rent Officers (Housing Benefit
Functions) Order 1997, Schedule 3B). The cap binds in central London, so
those published rates are a direct test of it.
"""

import pytest

from policyengine_uk import Simulation


# Weekly published rates for 2024/25, which SI 2025/5 and SI 2026/5 carry
# forward unchanged into 2025/26 and 2026/27.
CAPPED_RATES = [
    ("CENTRAL_LONDON", "B", 331.39),
    ("CENTRAL_LONDON", "C", 412.86),
    ("CENTRAL_LONDON", "D", 497.10),
    ("CENTRAL_LONDON", "E", 704.22),
    ("INNER_EAST_LONDON", "B", 331.39),
    ("INNER_EAST_LONDON", "D", 497.10),
]


def _weekly_rate(year: int, brma: str, category: str) -> float:
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
    annual = Simulation(situation=situation).calculate("BRMA_LHA_rate", year)[0]
    return float(annual) / 52


@pytest.mark.parametrize("brma,category,published", CAPPED_RATES)
@pytest.mark.parametrize("year", [2024, 2025, 2026])
def test_capped_rates_match_published(brma, category, published, year):
    assert _weekly_rate(year, brma, category) == pytest.approx(published, abs=0.01)


def test_cap_does_not_bind_below_the_percentile():
    """Category A in central London is set by the percentile, not the cap."""
    assert _weekly_rate(2024, "CENTRAL_LONDON", "A") < 331.39


def test_a_later_cap_change_cannot_move_a_frozen_rate():
    """Frozen rates are held at the level last determined.

    Every input to the determination — including the national maximum — is
    therefore read at the determination year, so changing a cap in a frozen
    year must leave the rate alone.
    """
    situation = {
        "people": {"person": {"age": {2025: 35}}},
        "benunits": {"benunit": {"members": ["person"], "LHA_category": {2025: "B"}}},
        "households": {
            "household": {
                "members": ["person"],
                "brma": {2025: "CENTRAL_LONDON"},
                "tenure_type": {2025: "RENT_PRIVATELY"},
                "rent": {2025: 100_000},
            }
        },
    }

    def weekly(reform):
        annual = Simulation(situation=situation, reform=reform).calculate(
            "BRMA_LHA_rate", 2025
        )[0]
        return float(annual) / 52

    baseline = weekly(None)
    slashed = weekly({"gov.dwp.LHA.maximum.B": {"2025": 100}})

    assert baseline == pytest.approx(331.39, abs=0.01)
    assert slashed == pytest.approx(baseline, abs=0.01)
