"""A unit's advance repayment input must retain its own missingness.

Core creates an input array for the whole population when any benefit unit
supplies a value. Omitted units must still use their legacy cash estimate,
while an explicitly supplied zero must suppress advance repayments.
"""

import numpy as np
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
FALLBACK = 0.1 * 400.14 * 12
COMBINATIONS = [
    "NONE",
    "ADVANCE_ONLY",
    "THIRD_PARTY_ONLY",
    "GOVERNMENT_ONLY",
    "ADVANCE_AND_GOVERNMENT",
    "ADVANCE_AND_THIRD_PARTY",
    "THIRD_PARTY_AND_GOVERNMENT",
    "ALL_THREE",
]


def situation(amounts, year=YEAR, age=30, latent=0.1, combination="ADVANCE_ONLY"):
    people, benunits, households = {}, {}, {}
    for i, amount in enumerate(amounts):
        person = f"person_{i}"
        people[person] = {"age": {year: age}}
        unit = {
            "members": [person],
            "would_claim_uc": {year: True},
            "universal_credit_pre_benefit_cap": {year: 6_000},
            "uc_benefit_cap_reduction": {year: 0},
            "uc_latent_deduction_rate": {year: latent},
            "uc_deduction_combination": {year: combination},
            # The latent rate counts only for a unit with the flag (#2739).
            "uc_has_deduction": {year: True},
        }
        if amount is not None:
            unit["uc_advance_repayment_amount"] = {year: amount}
        benunits[f"benunit_{i}"] = unit
        households[f"household_{i}"] = {"members": [person]}
    return {"people": people, "benunits": benunits, "households": households}


@pytest.mark.parametrize(
    "amounts, expected",
    [
        ([0, None], [0, FALLBACK]),
        ([None, 0], [FALLBACK, 0]),
        ([None, None], [FALLBACK, FALLBACK]),
        ([0, 0], [0, 0]),
        ([120, 240], [120, 240]),
        ([-1, 0], [FALLBACK, 0]),
        ([-1, -1], [FALLBACK, FALLBACK]),
    ],
    ids=[
        "zero-then-missing",
        "missing-then-zero",
        "fully-unsupplied",
        "fully-supplied-zero",
        "fully-supplied-positive",
        "sentinel-and-zero",
        "fully-supplied-sentinels",
    ],
)
def test_each_unit_resolves_its_own_advance_amount(amounts, expected):
    simulation = Simulation(situation=situation(amounts))
    np.testing.assert_allclose(
        simulation.calculate("uc_deductions", YEAR), expected, rtol=1e-6, atol=1e-3
    )


cash = st.integers(1, 300_000).map(lambda pennies: pennies / 100)
optional_cash = st.one_of(st.sampled_from([None, -1.0, 0.0]), cash)


@settings(max_examples=12, deadline=None, derandomize=True)
@given(
    target=optional_cash,
    peers=st.lists(optional_cash, min_size=1, max_size=4),
    position=st.integers(0, 4),
    age=st.integers(18, 60),
    latent=st.floats(0, 0.4, allow_nan=False, allow_infinity=False),
    combination=st.sampled_from(COMBINATIONS),
    year=st.sampled_from([2025, 2026]),
)
@example(
    target=None,
    peers=[0],
    position=1,
    age=30,
    latent=0.1,
    combination="ADVANCE_ONLY",
    year=2025,
)
@example(
    target=None,
    peers=[None, 120],
    position=0,
    age=24,
    latent=0.2,
    combination="ALL_THREE",
    year=2026,
)
@example(
    target=0,
    peers=[0, 120],
    position=1,
    age=30,
    latent=0.1,
    combination="ADVANCE_ONLY",
    year=2025,
)
@example(
    target=120,
    peers=[0, 240],
    position=2,
    age=30,
    latent=0.1,
    combination="ADVANCE_AND_GOVERNMENT",
    year=2025,
)
@example(
    target=-1,
    peers=[0],
    position=0,
    age=30,
    latent=0.1,
    combination="ADVANCE_ONLY",
    year=2025,
)
def test_advance_deduction_is_independent_of_peers_supplied_cash(
    target, peers, position, age, latent, combination, year
):
    """Change only other units' supplied cash; retain the target's deduction."""
    target_index = position % (len(peers) + 1)
    missing_peers = [None] * len(peers)
    supplied_peers = peers.copy()
    missing_peers.insert(target_index, target)
    supplied_peers.insert(target_index, target)

    def deduction(amounts):
        simulation = Simulation(
            situation=situation(amounts, year, age, latent, combination)
        )
        return simulation.calculate("uc_deductions", year)[target_index]

    assert deduction(supplied_peers) == pytest.approx(
        deduction(missing_peers), rel=1e-6, abs=1e-3
    )
