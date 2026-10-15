"""A dated reform's returned modifier works on an already-built simulation.

Construction still writes statutory dates before annualisation. A modifier
used separately instead follows Scenario.apply's annualised override reading.
"""

import datetime
import logging

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.scenarios.uc_reform import add_universal_credit_reform
from policyengine_uk.utils.dated_reforms import ReformPeriodWarning
from policyengine_uk.utils.scenario import Scenario


BASIC_RATE = "gov.hmrc.income_tax.rates.uk[0].rate"
PERSONAL_ALLOWANCE = "gov.hmrc.income_tax.allowances.personal_allowance.amount"
VAT_RATE = "gov.hmrc.vat.standard_rate"
NEW_CLAIMANT_AMOUNT = "gov.dwp.universal_credit.rebalancing.new_claimant_health_element"
YEARS = (2026, 2027)
SITUATION = {
    "people": {
        "claimant": {
            "age": {year: 35 for year in YEARS},
            "uc_limited_capability_for_WRA": {year: True for year in YEARS},
        }
    },
    "benunits": {
        "benunit": {
            "members": ["claimant"],
            "would_claim_uc": {year: True for year in YEARS},
            "uc_receives_new_claimant_health_element": {year: True for year in YEARS},
        }
    },
    "households": {"household": {"members": ["claimant"]}},
}
HEALTH_REFORM = {
    NEW_CLAIMANT_AMOUNT: {
        "2026-01-01.2026-12-31": 438.95,
        "2027-01-01.2027-12-31": 455.0,
    }
}


def parameter(simulation, path, date):
    return simulation.tax_benefit_system.parameters.get_child(path)(date)


@pytest.fixture(scope="module")
def baseline():
    return Simulation(situation=SITUATION)


@pytest.mark.parametrize("reform_class", [False, True])
def test_scorecard_modifier_changes_parameters_and_lcwra(baseline, reform_class):
    simulation = baseline.clone()
    original = [simulation.calculate("uc_LCWRA_element", y).copy() for y in YEARS]
    reform = Reform.from_dict(HEALTH_REFORM) if reform_class else HEALTH_REFORM

    Scenario.from_reform(reform).simulation_modifier(simulation)
    simulation.tax_benefit_system.reset_parameter_caches()
    add_universal_credit_reform(simulation)

    for year, monthly, previous in zip(YEARS, (438.95, 455.0), original):
        assert parameter(simulation, NEW_CLAIMANT_AMOUNT, str(year)) == monthly
        amount = simulation.calculate("uc_LCWRA_element", year)
        np.testing.assert_allclose(amount, monthly * 12)
        assert np.all(amount > previous)


@pytest.mark.parametrize("before_data_load", [False, True])
def test_scorecard_modifier_wrapped_in_user_scenario(before_data_load):
    def modifier(simulation):
        Scenario.from_reform(HEALTH_REFORM).simulation_modifier(simulation)
        simulation.tax_benefit_system.reset_parameter_caches()
        if getattr(simulation, "populations", None) is not None:
            add_universal_credit_reform(simulation)

    simulation = Simulation(
        situation=SITUATION,
        scenario=Scenario(
            simulation_modifier=modifier,
            applied_before_data_load=before_data_load,
        ),
    )
    for year, monthly in zip(YEARS, (438.95, 455.0)):
        assert parameter(simulation, NEW_CLAIMANT_AMOUNT, str(year)) == monthly
        np.testing.assert_allclose(
            simulation.calculate("uc_LCWRA_element", year), monthly * 12
        )


@st.composite
def annualised_changes(draw):
    path = draw(
        st.sampled_from([BASIC_RATE, PERSONAL_ALLOWANCE, VAT_RATE, NEW_CLAIMANT_AMOUNT])
    )
    start = draw(st.dates(datetime.date(2023, 1, 1), datetime.date(2032, 12, 31)))
    single_day = draw(st.booleans())
    stop = start if single_day else draw(st.dates(start, datetime.date(2032, 12, 31)))
    key = str(start) if single_day else f"{start}.{stop}"
    value = draw(st.integers(1, 100_000)) / 100
    contains_new_year = any(
        start <= datetime.date(year, 1, 1) <= stop
        for year in range(start.year, stop.year + 1)
    )
    return path, key, value, contains_new_year


@settings(
    max_examples=24,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(change=annualised_changes())
def test_modifier_matches_scenario_apply_on_built_parameters(baseline, change):
    path, key, value, contains_new_year = change
    scenario = Scenario.from_reform({path: {key: value}})
    direct, applied = baseline.clone(), baseline.clone()
    if not contains_new_year:
        for simulation, operation in (
            (direct, scenario.simulation_modifier),
            (applied, scenario.apply),
        ):
            with pytest.raises(ValueError) as error:
                operation(simulation)
            assert path in str(error.value)
            assert key in str(error.value)
        return

    scenario.simulation_modifier(direct)
    scenario.apply(applied)
    instants = [
        f"{year}-{month_day}"
        for year in range(2023, 2033)
        for month_day in ("01-01", "04-30", "07-01", "12-31")
    ]
    for date in instants:
        assert parameter(direct, path, date) == parameter(applied, path, date)


@pytest.mark.parametrize("operation", ["simulation_modifier", "apply"])
def test_built_override_warns_about_annualisation(baseline, caplog, operation):
    simulation = baseline.clone()
    scenario = Scenario.from_reform({BASIC_RATE: {"2026-01-01.2026-12-31": 0.31}})
    with caplog.at_level(logging.WARNING, logger="policyengine_uk.utils.scenario"):
        getattr(scenario, operation)(simulation)
    assert "dated reform keys are not annualised again" in caplog.text
    assert parameter(simulation, BASIC_RATE, "2026-01-01") == 0.31


@pytest.mark.parametrize("operation", ["simulation_modifier", "apply"])
@pytest.mark.parametrize("key", ["2026-04-06", "2026-04-06.2026-12-31"])
def test_built_override_rejects_key_that_changes_no_fiscal_year(
    baseline, operation, key
):
    simulation = baseline.clone()
    scenario = Scenario.from_reform({BASIC_RATE: {key: 0.31}})
    with pytest.raises(ValueError) as error:
        getattr(scenario, operation)(simulation)
    assert BASIC_RATE in str(error.value)
    assert key in str(error.value)


@pytest.mark.parametrize("before_data_load", [False, True])
@pytest.mark.parametrize("key", ["2026-04-06", "2026-04-06.2026-12-31"])
def test_external_modifier_wrapped_at_build_rejects_unreadable_window(
    before_data_load, key
):
    def modifier(simulation):
        Scenario.from_reform({BASIC_RATE: {key: 0.31}}).simulation_modifier(simulation)

    with pytest.raises(ValueError) as error:
        Simulation(
            situation=SITUATION,
            scenario=Scenario(
                simulation_modifier=modifier,
                applied_before_data_load=before_data_load,
            ),
        )
    assert BASIC_RATE in str(error.value)
    assert key in str(error.value)


@pytest.mark.parametrize("before_data_load", [False, True])
def test_own_single_day_modifier_at_build_retains_the_legacy_reading(before_data_load):
    scenario = Scenario.from_reform({BASIC_RATE: {"2026-04-06": 0.31}})
    scenario.applied_before_data_load = before_data_load
    with pytest.warns(ReformPeriodWarning):
        simulation = Simulation(situation=SITUATION, scenario=scenario)
    assert parameter(simulation, BASIC_RATE, "2026-01-01") == 0.20
    assert parameter(simulation, BASIC_RATE, "2026-04-06") == 0.31


@pytest.mark.parametrize("operation", ["simulation_modifier", "apply"])
def test_invalid_override_reports_every_path_without_partial_changes(
    baseline, operation
):
    simulation = baseline.clone()
    missing = (
        "gov.dwp.universal_credit.no_such_parameter",
        "gov.hmrc.no_such_parameter",
    )
    before = parameter(simulation, BASIC_RATE, "2026-01-01")
    changes = {BASIC_RATE: {"2026-01-01.2026-12-31": 0.31}}
    changes.update({path: {"2026-01-01.2026-12-31": 1} for path in missing})
    with pytest.raises(ValueError) as error:
        getattr(Scenario.from_reform(changes), operation)(simulation)
    for path in missing:
        assert path in str(error.value)
    assert parameter(simulation, BASIC_RATE, "2026-01-01") == before


@pytest.mark.parametrize("operation", ["simulation_modifier", "apply"])
def test_malformed_keys_report_every_path_without_partial_changes(baseline, operation):
    simulation = baseline.clone()
    changes = {BASIC_RATE: {"not-a-period": 0.31}, VAT_RATE: {"bad": 0.27}}
    before = [parameter(simulation, path, "2026-01-01") for path in changes]
    with pytest.raises(ValueError) as error:
        getattr(Scenario.from_reform(changes), operation)(simulation)
    for path, values in changes.items():
        assert path in str(error.value)
        assert next(iter(values)) in str(error.value)
    assert [parameter(simulation, path, "2026-01-01") for path in changes] == before


@pytest.mark.parametrize("operation", ["simulation_modifier", "apply"])
def test_malformed_core_keys_roll_back_and_report_every_path(baseline, operation):
    simulation = baseline.clone()
    malformed = {BASIC_RATE: {"not-a-period": 0.31}, VAT_RATE: {"bad": 0.27}}
    changes = {PERSONAL_ALLOWANCE: {"2026": 13_000}, **malformed}
    before = [parameter(simulation, path, "2026-01-01") for path in changes]
    overrides = list(simulation.tax_benefit_system.legacy_overrides)
    scenario = Scenario.from_reform(Reform.from_dict(changes))
    with pytest.raises(ValueError) as error:
        getattr(scenario, operation)(simulation)
    for path, values in malformed.items():
        assert path in str(error.value)
        assert next(iter(values)) in str(error.value)
    assert [parameter(simulation, path, "2026-01-01") for path in changes] == before
    assert simulation.tax_benefit_system.legacy_overrides == overrides


def test_modifier_only_overrides_changes_missing_from_the_system():
    written = {BASIC_RATE: {"2026-04-06.2027-04-05": 0.31}}
    simulation = Simulation(
        situation=SITUATION,
        reform=({VAT_RATE: {"2026": 0.22}}, written),
    )
    changes = {**written, NEW_CLAIMANT_AMOUNT: HEALTH_REFORM[NEW_CLAIMANT_AMOUNT]}
    Scenario.from_reform(changes).simulation_modifier(simulation)
    assert parameter(simulation, BASIC_RATE, "2026-01-01") == 0.31
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.20
    assert parameter(simulation, NEW_CLAIMANT_AMOUNT, "2026-01-01") == 438.95
    assert parameter(simulation, NEW_CLAIMANT_AMOUNT, "2027-01-01") == 455.0
    assert {item.path for item in simulation.tax_benefit_system.legacy_overrides} == {
        NEW_CLAIMANT_AMOUNT
    }


def test_reform_from_dict_modifier_preserves_its_onwards_reading(baseline):
    simulation = baseline.clone()
    scenario = Scenario.from_reform(Reform.from_dict({BASIC_RATE: {"2026": 0.31}}))
    scenario.simulation_modifier(simulation)
    assert parameter(simulation, BASIC_RATE, "2025-01-01") == 0.20
    for year in range(2026, 2033):
        assert parameter(simulation, BASIC_RATE, str(year)) == 0.31


@pytest.mark.parametrize(
    "spec",
    [
        pytest.param({"ETERNITY": 0.31}, id="eternity"),
        pytest.param(0.31, id="scalar"),
        pytest.param({"2026": 0.31}, id="bare_year"),
        pytest.param({"2026-01": 0.31}, id="january_month"),
        pytest.param({"2026-04-06": 0.31}, id="day_onwards"),
    ],
)
def test_reform_from_dict_modifier_matches_apply_for_core_period_readings(
    baseline, spec
):
    scenario = Scenario.from_reform(Reform.from_dict({BASIC_RATE: spec}))
    direct, applied = baseline.clone(), baseline.clone()
    scenario.simulation_modifier(direct)
    scenario.apply(applied)
    for year in range(2023, 2033):
        for month_day in ("01-01", "01-31", "02-01", "04-06", "12-31"):
            date = f"{year}-{month_day}"
            assert parameter(direct, BASIC_RATE, date) == parameter(
                applied, BASIC_RATE, date
            )
    assert (
        parameter(
            direct,
            BASIC_RATE,
            "2026-01-01"
            if isinstance(spec, dict) and "2026-01" in spec
            else "2027-01-01",
        )
        == 0.31
    )


@pytest.mark.parametrize("before_data_load", [False, True])
@pytest.mark.parametrize("representation", ["dict", "class", "repeated_tuple", "sum"])
def test_construction_retains_statutory_fiscal_years(before_data_load, representation):
    changes = {BASIC_RATE: {"2026-04-06.2027-04-05": 0.31}}
    if representation == "class":
        scenario = Scenario.from_reform(Reform.from_dict(changes))
    elif representation == "repeated_tuple":
        scenario = Scenario.from_reform((changes, changes))
    elif representation == "sum":
        scenario = Scenario.from_reform(changes) + Scenario.from_reform(changes)
    else:
        scenario = Scenario.from_reform(changes)
    scenario.applied_before_data_load = before_data_load
    simulation = Simulation(situation=SITUATION, scenario=scenario)
    assert parameter(simulation, BASIC_RATE, "2025-01-01") == 0.20
    assert parameter(simulation, BASIC_RATE, "2026-01-01") == 0.31
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.20
    assert simulation.tax_benefit_system.legacy_overrides == []


@pytest.mark.parametrize("before_first", [False, True])
def test_sum_keeps_each_parts_timing_and_copied_dated_reforms(before_first):
    seen = []
    before = Scenario.from_reform({BASIC_RATE: {"2026-04-06.2027-04-05": 0.31}})
    before.applied_before_data_load = True
    after = Scenario.from_reform({VAT_RATE: {"2027-04-06.2028-04-05": 0.27}})
    before = before + Scenario(
        simulation_modifier=lambda sim: seen.append(
            getattr(sim, "populations", None) is None
        ),
        applied_before_data_load=True,
    )
    after = after + Scenario(
        simulation_modifier=lambda sim: seen.append(
            getattr(sim, "populations", None) is None
        )
    )
    scenario = before + after if before_first else after + before
    simulation = Simulation(situation=SITUATION, scenario=scenario)
    assert seen == [True, False]
    assert parameter(simulation, BASIC_RATE, "2026-01-01") == 0.31
    assert parameter(simulation, BASIC_RATE, "2027-01-01") == 0.20
    assert parameter(simulation, VAT_RATE, "2027-01-01") == 0.27
    assert simulation.tax_benefit_system.legacy_overrides == []


@pytest.mark.parametrize("copy_kind", ["clone", "branch"])
def test_modifier_on_copy_of_simulation_built_with_reform_does_not_apply_twice(
    copy_kind,
):
    changes = {BASIC_RATE: {"2026-04-06.2027-04-05": 0.31}}
    original = Simulation(situation=SITUATION, reform=(changes, changes))
    simulation = (
        original.clone() if copy_kind == "clone" else original.get_branch("copy")
    )
    dates = [f"{year}-01-01" for year in range(2023, 2033)]
    before = [parameter(simulation, BASIC_RATE, date) for date in dates]
    assignments = list(simulation.tax_benefit_system.dated_assignments)

    # A fresh Scenario owns a different DatedReform object; the assignment
    # written onto the system, including either repeated occurrence, matters.
    Scenario.from_reform(changes).simulation_modifier(simulation)

    assert [parameter(simulation, BASIC_RATE, date) for date in dates] == before
    assert simulation.tax_benefit_system.dated_assignments == assignments
    assert simulation.tax_benefit_system.legacy_overrides == []
