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
