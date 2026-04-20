"""Verify the triple lock and downstream state pension amounts match published
DWP / OBR uprating outturn for years where the actual rate is known.

Issue #953: previously the triple lock was computed from OBR calendar-year
average earnings growth, which differs from the May-July AWE window DWP uses
for the actual triple lock. That left every uprating year ~0.5-1.2pp off.
"""

import pytest

from policyengine_uk.system import system


# (year, expected uprating rate). Sources are linked in
# parameters/gov/dwp/state_pension/triple_lock/outturn.yaml.
OUTTURN_RATES = [
    (2022, 0.031),
    (2023, 0.101),
    (2024, 0.085),
    (2025, 0.041),
    (2026, 0.048),
]

# (year, expected weekly £). Cross-referenced against gov.uk benefit and
# pension rates publications.
BASIC_STATE_PENSION_WEEKLY = [
    (2024, 169.50),
    (2025, 176.45),
    (2026, 184.90),
]

NEW_STATE_PENSION_WEEKLY = [
    (2024, 221.20),
    (2025, 230.25),
    (2026, 241.30),
]


@pytest.mark.parametrize("year, expected", OUTTURN_RATES)
def test_triple_lock_yoy_matches_published_outturn(year, expected):
    """The generated triple lock yoy parameter should equal the DWP-announced
    rate for years where outturn is known."""
    yoy = system.parameters.gov.economic_assumptions.yoy_growth.triple_lock(
        f"{year}-01-01"
    )
    assert yoy == pytest.approx(expected, abs=1e-3)


@pytest.mark.parametrize("year, expected", BASIC_STATE_PENSION_WEEKLY)
def test_basic_state_pension_matches_published_rate(year, expected):
    weekly = system.parameters.gov.dwp.state_pension.basic_state_pension.amount(
        f"{year}-04-01"
    )
    assert weekly == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize("year, expected", NEW_STATE_PENSION_WEEKLY)
def test_new_state_pension_matches_published_rate(year, expected):
    weekly = system.parameters.gov.dwp.state_pension.new_state_pension.amount(
        f"{year}-04-01"
    )
    assert weekly == pytest.approx(expected, abs=0.01)
