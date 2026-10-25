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
