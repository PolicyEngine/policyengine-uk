"""Smoke tests against the *latest* published enhanced FRS dataset.

These complement the pinned microsimulation tests in
``policyengine_uk/tests/microsimulation/`` by exercising the model against
whatever is currently on HuggingFace `main`, so that a silent break at the
model/data boundary (e.g. the model expecting an input column the rebuilt
dataset hasn't populated) shows up in CI rather than after a release.

Bounds are deliberately wide — they catch catastrophic failures (e.g.
``is_parent`` defaulting to zero, UC aggregate collapsing by ~£25 bn) without
tripping on normal calibration noise.

Skipped unless ``HUGGING_FACE_TOKEN`` or ``POLICYENGINE_UK_DEFAULT_DATASET`` is
set, via the ``microsimulation`` marker configured in ``conftest.py``.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from policyengine_uk import Microsimulation


LATEST_DATASET_URL = (
    "hf://policyengine/policyengine-uk-data-private/enhanced_frs_2023_24.h5"
)
YEAR = 2025


@pytest.fixture(scope="module")
def sim() -> Microsimulation:
    """Simulation built against the unpinned latest dataset.

    Overrides any pinned-version dataset set in conftest.py so the test
    exercises whatever is on HuggingFace ``main`` right now.
    """
    os.environ["POLICYENGINE_UK_DEFAULT_DATASET"] = LATEST_DATASET_URL
    return Microsimulation()


def _weighted(sim: Microsimulation, variable: str, period: int = YEAR) -> float:
    values = np.asarray(sim.calculate(variable, period).values, dtype=float)
    n = len(values)
    for weight_var in ("person_weight", "benunit_weight", "household_weight"):
        weight = np.asarray(sim.calculate(weight_var, period).values, dtype=float)
        if len(weight) == n:
            return float((values * weight).sum())
    raise AssertionError(
        f"No entity weight matches length {n} for variable {variable!r}"
    )


@pytest.mark.microsimulation
def test_population_totals_are_plausible(sim):
    """UK weighted population and household counts sit in sensible bounds."""
    people = float(np.asarray(sim.calculate("person_weight", YEAR).values).sum())
    benunits = float(np.asarray(sim.calculate("benunit_weight", YEAR).values).sum())
    households = float(np.asarray(sim.calculate("household_weight", YEAR).values).sum())

    # ONS mid-2024 estimate ~68.9M; OBR forecasts 2025 ≈ 69.5M.
    assert 65e6 < people < 75e6, f"People total {people:.3g} outside 65-75M"
    # FRS implies ~33-35M benefit units; ONS ~28M households.
    assert 30e6 < benunits < 38e6, f"Benefit units total {benunits:.3g} outside 30-38M"
    assert 26e6 < households < 34e6, f"Household total {households:.3g} outside 26-34M"


@pytest.mark.microsimulation
def test_is_parent_is_populated(sim):
    """``is_parent`` must come from FRS microdata, not default to zero.

    Catches the PolicyEngine/policyengine-uk#1595 failure mode where the
    inferred-formula was removed but a rebuilt dataset hadn't yet populated
    the column.
    """
    parents = _weighted(sim, "is_parent")
    # UK has ~15M parents of dependent children — anything under a few
    # million indicates the column defaulted rather than loaded.
    assert parents > 10e6, (
        f"is_parent weighted total {parents:.3g} is too low — the variable "
        "is likely defaulting to zero because the input column is missing."
    )


@pytest.mark.microsimulation
def test_universal_credit_aggregate_in_range(sim):
    """UC aggregate sits within plausible range of the OBR forecast.

    Catches cases where capital-limit or other model logic interacts
    badly with the data (e.g. stale savings imputations producing
    sub-£60bn UC aggregates when the target is ~£74bn).
    """
    uc = _weighted(sim, "universal_credit")
    # OBR Nov 2025 EFO calibration target is ~£74bn. Bounds allow for
    # +/-25% drift either side before failing.
    assert 55e9 < uc < 95e9, (
        f"Universal credit aggregate £{uc / 1e9:.1f}bn outside "
        "£55-£95bn plausibility range"
    )


@pytest.mark.microsimulation
def test_core_benefits_are_nonzero(sim):
    """Core benefit aggregates must produce output, not collapse to zero."""
    for variable, lower in [
        ("state_pension", 100e9),
        ("child_benefit", 10e9),
        ("pension_credit", 2e9),
    ]:
        total = _weighted(sim, variable)
        assert total > lower, (
            f"{variable} aggregate £{total / 1e9:.2g}bn below £{lower / 1e9:.0f}bn floor"
        )


@pytest.mark.microsimulation
def test_childcare_entitlement_populated(sim):
    """Extended childcare entitlement must reach >0 benefit units.

    Catches the downstream failure when ``is_parent`` is defaulted —
    every childcare-eligibility chain collapses to zero.
    """
    eligible = _weighted(sim, "extended_childcare_entitlement_eligible")
    assert eligible > 500_000, (
        f"extended_childcare_entitlement_eligible weighted total "
        f"{eligible:.3g} implies the childcare chain is broken"
    )
