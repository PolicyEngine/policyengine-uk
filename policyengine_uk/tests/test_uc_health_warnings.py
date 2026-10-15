"""LCWRA amount changes warn when rebalancing supplies the amount paid."""

import warnings
from datetime import date, timedelta

import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Scenario, Simulation
import policyengine_uk.scenarios.uc_reform as uc_reform

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

AMOUNT = "gov.dwp.universal_credit.elements.disabled.amount"
ACTIVE = "gov.dwp.universal_credit.rebalancing.active"
PROTECTED = "gov.dwp.universal_credit.rebalancing.protected_health_element"
NEW_CLAIMANT = "gov.dwp.universal_credit.rebalancing.new_claimant_health_element"
YEARS = range(2025, 2033)
SITUATION = {
    "people": {
        "adult": {
            "age": {year: 30 for year in YEARS},
            "uc_limited_capability_for_WRA": {year: True for year in YEARS},
        }
    },
    "benunits": {"benunit": {"members": ["adult"]}},
    "households": {"household": {"members": ["adult"]}},
}


def _warning_type():
    # On main the regression must fail because no warning is emitted.
    return getattr(uc_reform, "UCHealthElementOverrideWarning", UserWarning)


def _via_route(route, changes):
    if route == "reform_dict":
        return Simulation(situation=SITUATION, reform=changes)
    if route == "reform_class":
        return Simulation(situation=SITUATION, reform=Reform.from_dict(changes))
    if route == "parameter_changes":
        return Simulation(
            situation=SITUATION, scenario=Scenario(parameter_changes=changes)
        )
    if route == "tuple":
        return Simulation(situation=SITUATION, reform=(changes, changes))
    scenario = Scenario.from_reform(changes)
    if route == "sum":
        scenario = scenario + Scenario.from_reform(changes)
    if route == "before_load":
        scenario.applied_before_data_load = True
    if route in ("apply", "modifier"):
        sim = Simulation(situation=SITUATION)
        if route == "apply":
            scenario.apply(sim)
        else:
            scenario.simulation_modifier(sim)
        return sim
    return Simulation(situation=SITUATION, scenario=scenario)


ROUTES = (
    "reform_dict",
    "scenario",
    "reform_class",
    "parameter_changes",
    "before_load",
    "apply",
    "modifier",
    "tuple",
    "sum",
)


@pytest.mark.parametrize("route", ROUTES)
def test_amount_reform_warns_once_on_every_route(route):
    changes = {AMOUNT: {"2026-01-01.2028-12-31": 600}}
    with pytest.warns(_warning_type(), match="protected_health_element") as caught:
        _via_route(route, changes)

    health_warnings = [w for w in caught if issubclass(w.category, _warning_type())]
    assert len(health_warnings) == 1
    message = str(health_warnings[0].message)
    assert PROTECTED in message
    assert NEW_CLAIMANT in message
    assert all(str(year) in message for year in (2026, 2027, 2028))
    assert "2029" not in message


@pytest.mark.parametrize(
    "changes",
    [
        None,
        {NEW_CLAIMANT: {"2027-01-01.2027-12-31": 500}},
        {AMOUNT: {"2025-01-01.2025-12-31": 600}},
        {AMOUNT: {"2030-01-01.2030-12-31": 600}},
        {AMOUNT: {"2027-01-01.2027-12-31": 600}, ACTIVE: False},
    ],
)
def test_baseline_unrelated_outside_and_disabled_reforms_do_not_warn(changes):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        Simulation(situation=SITUATION, reform=changes)
    assert not [w for w in caught if issubclass(w.category, _warning_type())]


@pytest.mark.parametrize("route", ROUTES)
def test_active_false_in_the_same_reform_suppresses_the_warning(route):
    changes = {AMOUNT: {"2027-01-01.2027-12-31": 600}, ACTIVE: False}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _via_route(route, changes)
    assert not [w for w in caught if issubclass(w.category, _warning_type())]


def test_parameter_changes_apply_warns_on_the_built_simulation():
    sim = Simulation(situation=SITUATION)
    with pytest.warns(_warning_type(), match="2026, 2027, 2028, 2029"):
        Scenario(parameter_changes={AMOUNT: 600}).apply(sim)


def test_baseline_clone_can_warn_when_a_reform_is_applied():
    baseline = Simulation(situation=SITUATION).baseline
    with pytest.warns(_warning_type(), match="2027"):
        Scenario.from_reform({AMOUNT: {"2027-01-01.2027-12-31": 600}}).apply(baseline)


def test_the_warning_does_not_change_values():
    baseline = Simulation(situation=SITUATION)
    with pytest.warns(_warning_type(), match="protected_health_element"):
        reformed = Simulation(
            situation=SITUATION,
            reform={AMOUNT: {"2026-01-01.2029-12-31": 600}},
        )
    for year in range(2026, 2030):
        for variable in ("uc_LCWRA_element", "universal_credit"):
            np.testing.assert_array_equal(
                reformed.calculate(variable, year), baseline.calculate(variable, year)
            )


def test_warning_can_be_escalated_to_an_error():
    with warnings.catch_warnings():
        warnings.simplefilter("error", _warning_type())
        with pytest.raises(_warning_type(), match="new_claimant_health_element"):
            Simulation(
                situation=SITUATION,
                reform={AMOUNT: {"2027-01-01.2027-12-31": 600}},
            )


def test_warning_follows_the_years_used_by_the_rebalancing_loop(monkeypatch):
    monkeypatch.setattr(uc_reform, "REBALANCING_YEARS", (2025,), raising=False)
    with pytest.warns(_warning_type(), match="2025"):
        Simulation(
            situation=SITUATION,
            reform={AMOUNT: {"2025-01-01.2025-12-31": 600}},
        )


def test_warning_also_covers_an_extended_projection_horizon(monkeypatch):
    sim = Simulation(
        situation=SITUATION,
        reform={AMOUNT: {"2030-01-01.2030-12-31": 600}},
    )
    monkeypatch.setattr(uc_reform, "REBALANCING_YEARS", (2030,), raising=False)
    with pytest.warns(_warning_type(), match="2030"):
        warn = getattr(
            uc_reform,
            "warn_shadowed_lcwra_reform",
            uc_reform.add_universal_credit_reform,
        )
        warn(sim)


@pytest.mark.parametrize("key", ["2027", "2027-01-01", "2027-04-06.2028-04-05"])
def test_warning_uses_the_route_reading_of_period_keys(key):
    with pytest.warns(_warning_type(), match="2027") as caught:
        Simulation(situation=SITUATION, reform={AMOUNT: {key: 600}})
    message = str(caught[0].message)
    assert "2026" not in message
    assert "2028" not in message


def test_warning_names_only_the_years_still_active():
    with pytest.warns(_warning_type(), match="2026, 2028") as caught:
        Simulation(
            situation=SITUATION,
            reform={
                AMOUNT: {"2026-01-01.2028-12-31": 600},
                ACTIVE: {"2027-01-01.2027-12-31": False},
            },
        )
    assert "2027" not in str(caught[0].message)


def test_tuple_and_sum_defer_warning_until_active_override_runs():
    # Single-day changes run as overrides after the construction-time UC
    # modifier. They must be checked after the whole tuple or sum has run.
    amount = {AMOUNT: {"2027-01-01": 600}}
    disabled = {ACTIVE: {"2027-01-01": False}}
    for scenario in (
        Scenario.from_reform((amount, disabled)),
        Scenario.from_reform(amount) + Scenario.from_reform(disabled),
    ):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Simulation(situation=SITUATION, scenario=scenario)
        assert not [w for w in caught if issubclass(w.category, _warning_type())]


@settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@example(start=date(2027, 4, 30), length=0, active=[True] * 4)
@example(start=date(2027, 4, 29), length=0, active=[True] * 4)
@given(
    start=st.dates(min_value=date(2023, 1, 1), max_value=date(2032, 12, 31)),
    length=st.integers(0, 1_100),
    active=st.lists(st.booleans(), min_size=4, max_size=4),
)
def test_warning_iff_a_reformed_window_reaches_an_active_rebalancing_year(
    start, length, active
):
    stop = start + timedelta(days=length)
    changes = {
        AMOUNT: {f"{start}.{stop}": 600},
        ACTIVE: {
            f"{year}-01-01.{year}-12-31": enabled
            for year, enabled in zip(range(2026, 2030), active)
        },
    }
    expected_years = [
        year
        for year, enabled in zip(range(2026, 2030), active)
        if enabled and start <= date(year, 4, 30) <= stop
    ]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        Simulation(situation=SITUATION, reform=changes)
    health_warnings = [w for w in caught if issubclass(w.category, _warning_type())]
    assert bool(health_warnings) == bool(expected_years)
    if expected_years:
        assert len(health_warnings) == 1
        message = str(health_warnings[0].message)
        assert all(str(year) in message for year in expected_years)
