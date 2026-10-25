"""Construction modifiers retain explicit inputs and discard stale calculations.

All situations are synthetic households. A fixed Child Benefit addition changes
income but no marginal rate at these earnings, so it has only an income effect.
The equivalent parameter change supplies an independent route to that outcome.
"""

import copy

import numpy as np
import pytest
from policyengine_core.periods import period

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.model_api import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2027
CHILD_BENEFIT = "child_benefit"
ELDEST_AMOUNT = "gov.hmrc.child_benefit.amount.eldest"
RESPONSE = "employment_income_behavioral_response"
INCOME_TERM = "income_elasticity_lsr"
SUBSTITUTION_TERM = "substitution_elasticity_lsr"
ELASTICITIES = {
    "gov.simulation.labour_supply_responses.substitution_elasticity": {str(YEAR): 0.15},
    "gov.simulation.labour_supply_responses.income_elasticity": {str(YEAR): -0.05},
}


def family(years=(YEAR,)):
    return {
        "people": {
            "parent": {
                "age": {year: 30 for year in years},
                "gender": {year: "FEMALE" for year in years},
                "employment_income": {year: 25_000 for year in years},
                "hours_worked": {year: 1_500 for year in years},
            },
            "child": {"age": {year: 2 for year in years}},
        },
        "benunits": {
            "benunit": {
                "members": ["parent", "child"],
                "would_claim_child_benefit": {year: True for year in years},
            }
        },
        "households": {"household": {"members": ["parent", "child"]}},
    }


def values(simulation, variable, year=YEAR):
    return np.asarray(simulation.calculate(variable, year)).copy()


def add_benefit(simulation, *, read_first=True, years=(YEAR,), holder=False):
    for year in years:
        source = simulation if read_first else simulation.baseline
        benefit = values(source, CHILD_BENEFIT, year)
        if holder:
            simulation.get_holder(CHILD_BENEFIT).set_input(
                period(year), benefit + 1_000, simulation.branch_name
            )
        else:
            simulation.set_input(CHILD_BENEFIT, year, benefit + 1_000)


def parameter_benchmark(parameter_changes=None):
    baseline = Simulation(situation=family())
    weekly = baseline.tax_benefit_system.parameters.get_child(ELDEST_AMOUNT)(str(YEAR))
    return Simulation(
        situation=family(),
        scenario=Scenario(
            parameter_changes={
                **(parameter_changes or {}),
                ELDEST_AMOUNT: {str(YEAR): weekly + 1_000 / 52},
            }
        ),
    )


@pytest.mark.parametrize("holder", [False, True], ids=["simulation", "holder"])
@pytest.mark.parametrize(
    "years", [(YEAR,), (YEAR, YEAR + 1)], ids=["one-year", "two-years"]
)
def test_modifier_input_survives_reset(holder, years):
    simulation = Simulation(
        situation=family(years),
        scenario=Scenario(
            simulation_modifier=lambda sim: add_benefit(sim, holder=holder, years=years)
        ),
    )
    assert CHILD_BENEFIT in simulation.input_variables
    assert CHILD_BENEFIT not in simulation.baseline.input_variables
    simulation.reset_calculations()
    for year in years:
        np.testing.assert_allclose(
            values(simulation, CHILD_BENEFIT, year),
            values(simulation.baseline, CHILD_BENEFIT, year) + 1_000,
            atol=0.01,
        )


def test_modifier_inputs_exclude_calculated_intermediates():
    def modifier(simulation):
        values(simulation, "household_net_income")
        add_benefit(simulation)

    simulation = Simulation(
        situation=family(), scenario=Scenario(simulation_modifier=modifier)
    )
    names = set(simulation.input_variables) - set(simulation.baseline.input_variables)
    assert names == {CHILD_BENEFIT}
    assert not names.intersection(
        {"adjusted_net_income", "income_tax", "ni_class_1_employee"}
    )
    benchmark = parameter_benchmark()
    for variable in ("household_net_income", "income_tax", "adjusted_net_income"):
        np.testing.assert_allclose(
            values(simulation, variable), values(benchmark, variable), atol=0.01
        )


@pytest.mark.parametrize("dependent", ["household_net_income", "gov_balance"])
def test_modifier_recalculates_cached_dependents(dependent):
    def modifier(simulation):
        values(simulation, dependent)
        add_benefit(simulation)

    simulation = Simulation(
        situation=family(), scenario=Scenario(simulation_modifier=modifier)
    )
    expected = values(parameter_benchmark(), dependent)
    np.testing.assert_allclose(values(simulation, dependent), expected, atol=0.01)
    simulation.reset_calculations()
    np.testing.assert_allclose(values(simulation, dependent), expected, atol=0.01)


def test_modifier_keeps_overwritten_input_without_mutating_baseline():
    situation = family()
    situation["benunits"]["benunit"][CHILD_BENEFIT] = {YEAR: 500}
    original = copy.deepcopy(situation)
    captured = {}

    def modifier(simulation):
        captured["names"] = simulation.baseline.input_variables
        captured["recorded"] = list(simulation.baseline.input_variables)
        captured["net"] = values(simulation.baseline, "household_net_income")
        values(simulation, "household_net_income")
        add_benefit(simulation)

    simulation = Simulation(
        situation=situation, scenario=Scenario(simulation_modifier=modifier)
    )
    np.testing.assert_allclose(
        values(simulation, "household_net_income"), captured["net"] + 1_000, atol=0.01
    )
    simulation.reset_calculations()
    np.testing.assert_array_equal(values(simulation, CHILD_BENEFIT), [1_500])
    np.testing.assert_array_equal(values(simulation.baseline, CHILD_BENEFIT), [500])
    np.testing.assert_array_equal(
        values(simulation.baseline, "household_net_income"), captured["net"]
    )
    assert simulation.baseline.input_variables is captured["names"]
    assert captured["names"] == captured["recorded"]
    assert situation == original


@pytest.mark.parametrize("route", ["deleted", "clone", "branch", "calculated"])
def test_modifier_names_only_surviving_own_inputs(route):
    def modifier(simulation):
        if route == "deleted":
            simulation.set_input(CHILD_BENEFIT, YEAR, [5_000])
            simulation.delete_arrays(CHILD_BENEFIT, YEAR)
        elif route == "clone":
            simulation.clone().set_input(CHILD_BENEFIT, YEAR, [5_000])
        elif route == "branch":
            simulation.get_branch("modifier_other").set_input(
                CHILD_BENEFIT, YEAR, [5_000]
            )
        else:
            values(simulation, CHILD_BENEFIT)

    simulation = Simulation(
        situation=family(), scenario=Scenario(simulation_modifier=modifier)
    )
    assert simulation.input_variables == simulation.baseline.input_variables
    simulation.reset_calculations()
    np.testing.assert_array_equal(
        values(simulation, CHILD_BENEFIT), values(simulation.baseline, CHILD_BENEFIT)
    )


@pytest.mark.parametrize(
    "variable", ["marginal_tax_rate", "marginal_tax_rate_wrt_employer_cost"]
)
def test_modifier_fixed_child_benefit_addition_preserves_marginal_rates(variable):
    simulation = Simulation(
        situation=family(), scenario=Scenario(simulation_modifier=add_benefit)
    )
    np.testing.assert_allclose(
        values(simulation, variable), values(simulation.baseline, variable), atol=1e-5
    )
    np.testing.assert_allclose(
        values(simulation, variable), values(parameter_benchmark(), variable), atol=1e-5
    )


def test_fixed_tax_modifier_preserves_capital_gains_marginal_rate():
    situation = family()
    situation["people"]["parent"]["capital_gains"] = {YEAR: 10_000}

    def modifier(simulation):
        simulation.set_input("capital_gains_tax", YEAR, [5_000, 0])

    simulation = Simulation(
        situation=situation, scenario=Scenario(simulation_modifier=modifier)
    )
    assert values(simulation.baseline, "marginal_tax_rate_on_capital_gains")[0] > 0
    np.testing.assert_array_equal(
        values(simulation, "marginal_tax_rate_on_capital_gains"), [0, 0]
    )
    np.testing.assert_array_equal(values(simulation, "capital_gains_tax"), [5_000, 0])


def test_modifier_dynamics_preserves_benefit_and_income_only_response():
    simulation = Microsimulation(
        situation=family(),
        scenario=Scenario(
            parameter_changes={
                "gov.dynamic.obr_labour_supply_assumptions": {str(YEAR): True}
            },
            simulation_modifier=add_benefit,
        ),
    )
    expected = values(simulation.baseline, CHILD_BENEFIT) + 1_000
    progression = simulation.apply_dynamics(YEAR).progression
    np.testing.assert_allclose(values(simulation, CHILD_BENEFIT), expected, atol=0.01)
    np.testing.assert_allclose(
        progression["deriv_scenario"], progression["deriv_baseline"], atol=1e-5
    )
    np.testing.assert_allclose(progression["substitution_response"], 0, atol=0.01)
    assert (np.asarray(progression["income_response"]) < 0).all()
    np.testing.assert_allclose(
        progression["total_response"], progression["income_response"], atol=0.01
    )


@pytest.mark.parametrize(
    "read_first", [False, True], ids=["baseline-set", "read-then-set"]
)
@pytest.mark.parametrize(
    "first",
    [RESPONSE, "household_net_income"],
    ids=["response-first", "dependent-first"],
)
def test_modifier_response_matches_equivalent_parameter_change(read_first, first):
    simulation = Simulation(
        situation=family(),
        scenario=Scenario(
            parameter_changes=ELASTICITIES,
            simulation_modifier=lambda sim: add_benefit(sim, read_first=read_first),
        ),
    )
    benchmark = parameter_benchmark(ELASTICITIES)
    values(simulation, first)
    variables = (
        CHILD_BENEFIT,
        "household_net_income",
        "relative_income_change",
        "relative_wage_change",
        "marginal_tax_rate",
        RESPONSE,
    )
    expected = {variable: values(benchmark, variable) for variable in variables}
    assert expected[RESPONSE][0] < 0
    for variable in variables:
        np.testing.assert_allclose(
            values(simulation, variable),
            expected[variable],
            atol=0.01,
            rtol=1e-5,
            err_msg=variable,
        )
    np.testing.assert_allclose(values(simulation, "relative_wage_change"), 0, atol=1e-5)
    np.testing.assert_allclose(values(simulation, SUBSTITUTION_TERM), 0, atol=0.01)
    np.testing.assert_allclose(
        values(simulation, RESPONSE), values(simulation, INCOME_TERM), atol=0.01
    )
    simulation.reset_calculations()
    for variable in variables:
        np.testing.assert_allclose(
            values(simulation, variable),
            expected[variable],
            atol=0.01,
            rtol=1e-5,
            err_msg=variable,
        )


@pytest.mark.parametrize("scenario", [None, Scenario()], ids=["none", "empty"])
def test_no_modifier_keeps_existing_behavior(scenario):
    simulation = Simulation(situation=family(), scenario=scenario)
    np.testing.assert_array_equal(values(simulation, RESPONSE), [0, 0])
    np.testing.assert_array_equal(
        values(simulation, CHILD_BENEFIT), values(simulation.baseline, CHILD_BENEFIT)
    )
    assert simulation.input_variables == simulation.baseline.input_variables


def test_before_load_modifier_keeps_timing():
    calls = []

    def before(simulation):
        calls.append(("before", getattr(simulation, "populations", None)))

    def after(simulation):
        calls.append(("after", bool(simulation.populations)))

    simulation = Simulation(
        situation=family(),
        scenario=Scenario(simulation_modifier=before, applied_before_data_load=True)
        + Scenario(simulation_modifier=after),
    )
    assert calls == [("before", None), ("after", True)]
    assert simulation.input_variables == simulation.baseline.input_variables


@pytest.mark.parametrize(
    "variable", ["marginal_tax_rate", "marginal_tax_rate_wrt_employer_cost"]
)
def test_modifier_recalculates_cached_marginal_rate_branches(variable):
    years = (YEAR, YEAR + 1)
    warmed = []

    def modifier(simulation):
        for year in years:
            warmed.append(values(simulation, variable, year))
        add_benefit(simulation, years=years)

    simulation = Simulation(
        situation=family(years), scenario=Scenario(simulation_modifier=modifier)
    )
    assert len(warmed) == len(years)
    np.testing.assert_allclose(
        values(simulation, variable),
        values(parameter_benchmark(), variable),
        atol=1e-5,
    )
    for year in years:
        np.testing.assert_allclose(
            values(simulation, variable, year),
            values(simulation.baseline, variable, year),
            atol=1e-5,
        )
        np.testing.assert_allclose(
            values(simulation, CHILD_BENEFIT, year),
            values(simulation.baseline, CHILD_BENEFIT, year) + 1_000,
            atol=0.01,
        )


def test_modifier_recalculates_warmed_capital_gains_marginal_rate():
    situation = family()
    situation["people"]["parent"]["capital_gains"] = {YEAR: 10_000}

    def modifier(simulation):
        assert values(simulation, "marginal_tax_rate_on_capital_gains")[0] > 0
        # Gains-rate branches are removed by the formula after each step.
        assert not any(name.endswith("_cg_rise") for name in simulation.branches)
        simulation.set_input("capital_gains_tax", YEAR, [5_000, 0])

    simulation = Simulation(
        situation=situation, scenario=Scenario(simulation_modifier=modifier)
    )
    np.testing.assert_array_equal(
        values(simulation, "marginal_tax_rate_on_capital_gains"), [0, 0]
    )
    np.testing.assert_array_equal(values(simulation, "capital_gains_tax"), [5_000, 0])


@pytest.mark.parametrize(
    "variable, branch_name",
    [
        ("marginal_tax_rate", "adult_1_pay_rise"),
        ("marginal_tax_rate_wrt_employer_cost", "adult_1_employer_cost_mtr"),
    ],
)
def test_marginal_rate_keeps_an_existing_named_branch(variable, branch_name):
    simulation = Simulation(situation=family())
    existing = simulation.get_branch(branch_name)
    existing.set_input(CHILD_BENEFIT, YEAR, [5_000])
    expected = values(parameter_benchmark(), variable)

    np.testing.assert_allclose(values(simulation, variable), expected, atol=1e-5)

    assert set(simulation.branches) == {branch_name}
    assert simulation.branches[branch_name] is existing
    np.testing.assert_array_equal(values(existing, CHILD_BENEFIT), [5_000])


@pytest.mark.parametrize(
    "variable", ["marginal_tax_rate", "marginal_tax_rate_wrt_employer_cost"]
)
def test_marginal_rate_failure_detaches_its_scratch_branch(monkeypatch, variable):
    simulation = Simulation(situation=family())
    assert not simulation.branches
    set_input = Simulation.set_input

    def fail_pay_rise(branch, name, *args, **kwargs):
        if branch is not simulation and name == "employment_income":
            raise RuntimeError("synthetic pay-rise failure")
        return set_input(branch, name, *args, **kwargs)

    monkeypatch.setattr(Simulation, "set_input", fail_pay_rise)
    with pytest.raises(RuntimeError, match="synthetic pay-rise failure"):
        values(simulation, variable)
    assert not simulation.branches


def capital_gains_family():
    situation = family()
    situation["people"]["parent"]["capital_gains"] = {YEAR: 10_000}
    situation["people"]["partner"] = {
        "age": {YEAR: 35},
        "gender": {YEAR: "MALE"},
        "employment_income": {YEAR: 20_000},
        "capital_gains": {YEAR: 20_000},
    }
    situation["benunits"]["benunit"]["members"].append("partner")
    situation["households"]["household"]["members"].append("partner")
    return situation


@pytest.mark.parametrize("branch_name", ["adult_1_cg_rise", "adult_2_cg_rise"])
def test_capital_gains_rate_preserves_preoccupied_user_branch(branch_name):
    situation = capital_gains_family()
    expected = values(
        Simulation(situation=situation), "marginal_tax_rate_on_capital_gains"
    )
    assert (expected[[0, 2]] > 0).all()
    simulation = Simulation(situation=situation)
    original_gains = values(simulation, "capital_gains")
    original_benefit = values(simulation, CHILD_BENEFIT)
    original_names = list(simulation.input_variables)
    existing = simulation.get_branch(branch_name)
    existing.set_input(CHILD_BENEFIT, YEAR, [5_000])

    np.testing.assert_allclose(
        values(simulation, "marginal_tax_rate_on_capital_gains"),
        expected,
        atol=1e-5,
    )

    assert set(simulation.branches) == {branch_name}
    assert simulation.branches[branch_name] is existing
    np.testing.assert_array_equal(values(existing, CHILD_BENEFIT), [5_000])
    np.testing.assert_array_equal(values(simulation, "capital_gains"), original_gains)
    np.testing.assert_array_equal(values(simulation, CHILD_BENEFIT), original_benefit)
    assert simulation.input_variables == original_names


@pytest.mark.parametrize(
    "preoccupied", [False, True], ids=["unoccupied", "preoccupied"]
)
def test_capital_gains_rate_failure_preserves_user_branch_and_detaches_owned_scratch(
    monkeypatch, preoccupied
):
    situation = capital_gains_family()
    expected = values(
        Simulation(situation=situation), "marginal_tax_rate_on_capital_gains"
    )
    assert (expected[[0, 2]] > 0).all()
    simulation = Simulation(situation=situation)
    original_gains = values(simulation, "capital_gains")
    existing = None
    if preoccupied:
        existing = simulation.get_branch("adult_1_cg_rise")
        existing.set_input(CHILD_BENEFIT, YEAR, [5_000])
    original_branches = dict(simulation.branches)
    captured = {}
    set_input = Simulation.set_input

    def fail_gains_rise(branch, name, *args, **kwargs):
        if branch.parent_branch is simulation and name == "capital_gains":
            captured["branch"] = branch
            raise RuntimeError("synthetic capital-gains step failure")
        return set_input(branch, name, *args, **kwargs)

    with monkeypatch.context() as context:
        context.setattr(Simulation, "set_input", fail_gains_rise)
        with pytest.raises(RuntimeError, match="synthetic capital-gains step failure"):
            values(simulation, "marginal_tax_rate_on_capital_gains")

    assert captured["branch"] is not existing
    assert simulation.branches == original_branches
    assert all(
        branch is not captured["branch"] for branch in simulation.branches.values()
    )
    if existing is not None:
        assert simulation.branches["adult_1_cg_rise"] is existing
        np.testing.assert_array_equal(values(existing, CHILD_BENEFIT), [5_000])
    np.testing.assert_array_equal(values(simulation, "capital_gains"), original_gains)


def test_after_load_modifier_clears_calculated_values_once(monkeypatch):
    import policyengine_uk.simulation as uk_simulation

    expected = parameter_benchmark()
    expected_net = values(expected, "household_net_income")
    captured = {}
    cleanup_calls = []
    drop_calculated_values = uk_simulation.drop_calculated_values

    def counted_cleanup(owner):
        if owner is captured.get("owner") and captured.get("watch_cleanup"):
            cleanup_calls.append(owner)
        return drop_calculated_values(owner)

    def modifier(simulation):
        captured["owner"] = simulation
        captured["warm_net"] = values(simulation, "household_net_income")
        add_benefit(simulation)
        captured["watch_cleanup"] = True

    monkeypatch.setattr(uk_simulation, "drop_calculated_values", counted_cleanup)
    simulation = Simulation(
        situation=family(), scenario=Scenario(simulation_modifier=modifier)
    )
    assert len(cleanup_calls) == 1
    assert (expected_net > captured["warm_net"]).all()
    for _ in range(2):
        np.testing.assert_allclose(
            values(simulation, "household_net_income"), expected_net, atol=0.01
        )
        assert len(cleanup_calls) == 1


@pytest.mark.parametrize("failure", ["modifier", "cleanup"])
def test_after_load_cleanup_failure_keeps_pending_write(monkeypatch, failure):
    import policyengine_uk.simulation as uk_simulation

    expected = parameter_benchmark()
    expected_benefit = values(expected, CHILD_BENEFIT)
    expected_net = values(expected, "household_net_income")
    captured = {}
    cleanup_calls = []
    drop_calculated_values = uk_simulation.drop_calculated_values

    def fail_cleanup_once(owner):
        if owner is captured.get("owner") and captured.get("watch_cleanup"):
            cleanup_calls.append(owner)
            if failure == "cleanup" and len(cleanup_calls) == 1:
                raise RuntimeError("synthetic after-load failure")
        return drop_calculated_values(owner)

    def modifier(simulation):
        captured["owner"] = simulation
        captured["warm_net"] = values(simulation, "household_net_income")
        add_benefit(simulation)
        captured["stored_benefit"] = (
            simulation.get_holder(CHILD_BENEFIT)
            .get_array(period(YEAR), simulation.branch_name)
            .copy()
        )
        np.testing.assert_allclose(
            captured["stored_benefit"], expected_benefit, atol=0.01
        )
        captured["watch_cleanup"] = True
        if failure == "modifier":
            raise RuntimeError("synthetic after-load failure")

    monkeypatch.setattr(uk_simulation, "drop_calculated_values", fail_cleanup_once)
    with pytest.raises(RuntimeError, match="synthetic after-load failure"):
        Simulation(situation=family(), scenario=Scenario(simulation_modifier=modifier))

    simulation = captured["owner"]
    assert simulation._external_input_change_pending
    np.testing.assert_array_equal(
        simulation.get_holder(CHILD_BENEFIT).get_array(
            period(YEAR), simulation.branch_name
        ),
        captured["stored_benefit"],
    )
    assert (expected_net > captured["warm_net"]).all()
    np.testing.assert_allclose(
        values(simulation, "household_net_income"), expected_net, atol=0.01
    )
    assert not simulation._external_input_change_pending
    assert len(cleanup_calls) == (1 if failure == "modifier" else 2)


def test_default_baseline_clones_after_framework_input_drain(monkeypatch):
    import policyengine_uk.simulation as uk_simulation

    captured = {}
    cleanup_calls = []
    move_values = Simulation.move_values
    clone = Simulation.clone
    drop_calculated_values = uk_simulation.drop_calculated_values

    def observe_framework_inputs(owner, donor, target):
        result = move_values(owner, donor, target)
        if donor == "bus_fare_spending":
            captured["owner"] = owner
            assert owner._external_input_change_pending
            captured["health_element"] = (
                owner.get_holder("uc_LCWRA_element")
                .get_array(period(YEAR), owner.branch_name)
                .copy()
            )
        return result

    def counted_cleanup(owner):
        if owner is captured.get("owner"):
            cleanup_calls.append(owner)
        return drop_calculated_values(owner)

    def observe_clone(owner, *args, **kwargs):
        if owner is captured.get("owner"):
            assert not owner._external_input_change_pending
            assert cleanup_calls == [owner]
            captured["cloned"] = True
        return clone(owner, *args, **kwargs)

    monkeypatch.setattr(Simulation, "move_values", observe_framework_inputs)
    monkeypatch.setattr(Simulation, "clone", observe_clone)
    monkeypatch.setattr(uk_simulation, "drop_calculated_values", counted_cleanup)
    simulation = Simulation(situation=family())

    assert captured["cloned"]
    for owner in (simulation, simulation.baseline):
        assert not owner._external_input_change_pending
        np.testing.assert_array_equal(
            owner.get_holder("employment_income_before_lsr").get_array(
                period(YEAR), owner.branch_name
            ),
            [25_000, 0],
        )
        np.testing.assert_array_equal(
            owner.get_holder("uc_LCWRA_element").get_array(
                period(YEAR), owner.branch_name
            ),
            captured["health_element"],
        )


def test_default_constructor_first_reads_do_not_repeat_framework_drain(monkeypatch):
    import policyengine_uk.simulation as uk_simulation

    reference = Simulation(situation=family())
    reference.reset_calculations()
    reference.baseline.reset_calculations()
    expected = values(reference, "household_net_income")
    cleanup_calls = []
    drop_calculated_values = uk_simulation.drop_calculated_values

    def counted_cleanup(owner):
        cleanup_calls.append(owner)
        return drop_calculated_values(owner)

    simulation = Simulation(situation=family())
    monkeypatch.setattr(uk_simulation, "drop_calculated_values", counted_cleanup)
    for _ in range(2):
        for owner in (simulation, simulation.baseline):
            np.testing.assert_allclose(
                values(owner, "household_net_income"), expected, atol=0.01
            )
    assert cleanup_calls == []


def test_default_baseline_drain_failure_retains_pending_inputs(monkeypatch):
    import policyengine_uk.simulation as uk_simulation

    reference = Simulation(situation=family())
    reference.reset_calculations()
    expected_tax = values(reference, "income_tax")
    captured = {}
    cloned = []
    move_values = Simulation.move_values
    clone = Simulation.clone
    drop_calculated_values = uk_simulation.drop_calculated_values

    def observe_framework_inputs(owner, donor, target):
        result = move_values(owner, donor, target)
        if donor == "bus_fare_spending":
            captured["owner"] = owner
            captured["health_element"] = (
                owner.get_holder("uc_LCWRA_element")
                .get_array(period(YEAR), owner.branch_name)
                .copy()
            )
        return result

    def fail_terminal_cleanup(owner):
        if owner is captured.get("owner"):
            assert owner._external_input_change_pending
            raise RuntimeError("synthetic terminal framework drain failure")
        return drop_calculated_values(owner)

    def observe_clone(owner, *args, **kwargs):
        if owner is captured.get("owner"):
            cloned.append(owner)
        return clone(owner, *args, **kwargs)

    with monkeypatch.context() as context:
        context.setattr(Simulation, "move_values", observe_framework_inputs)
        context.setattr(Simulation, "clone", observe_clone)
        context.setattr(uk_simulation, "drop_calculated_values", fail_terminal_cleanup)
        with pytest.raises(
            RuntimeError, match="synthetic terminal framework drain failure"
        ):
            Simulation(situation=family())

    simulation = captured["owner"]
    assert simulation._external_input_change_pending
    assert "baseline" not in simulation.__dict__
    assert cloned == []
    np.testing.assert_array_equal(
        simulation.get_holder("employment_income_before_lsr").get_array(
            period(YEAR), simulation.branch_name
        ),
        [25_000, 0],
    )
    np.testing.assert_array_equal(
        simulation.get_holder("uc_LCWRA_element").get_array(
            period(YEAR), simulation.branch_name
        ),
        captured["health_element"],
    )
    np.testing.assert_allclose(
        values(simulation, "income_tax"), expected_tax, atol=0.01
    )
    assert not simulation._external_input_change_pending
