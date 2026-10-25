"""Public synthetic regressions for callbacks on an already-built UK model."""

import copy

import numpy as np
import pytest

from policyengine_uk import Microsimulation, Simulation
from policyengine_uk.scenarios.pip_reform import modify_simulation as phase_in_pip

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2027
BENEFIT = "child_benefit"
CLAIM = "would_claim_child_benefit"
RESPONSE = "employment_income_behavioral_response"
ELDEST = "gov.hmrc.child_benefit.amount.eldest"
ELASTICITIES = {
    "gov.simulation.labour_supply_responses.substitution_elasticity": {str(YEAR): 0.15},
    "gov.simulation.labour_supply_responses.income_elasticity": {str(YEAR): -0.05},
}
RATES = (
    "marginal_tax_rate",
    "marginal_tax_rate_wrt_employer_cost",
    "marginal_tax_rate_on_capital_gains",
)


def family(years=(YEAR,)):
    return {
        "people": {
            "parent": {
                "age": {year: 30 for year in years},
                "gender": {year: "FEMALE" for year in years},
                "employment_income": {year: 25_000 for year in years},
                "hours_worked": {year: 1_500 for year in years},
                "capital_gains": {year: 10_000 for year in years},
            },
            "child": {"age": {year: 2 for year in years}},
        },
        "benunits": {"family": {"members": ["parent", "child"]}},
        "households": {"home": {"members": ["parent", "child"]}},
    }


def values(simulation, variable, year=YEAR):
    return np.asarray(simulation.calculate(variable, year)).copy()


def add_benefit(simulation, read_first=True, years=(YEAR,)):
    for year in years:
        source = simulation if read_first else simulation.baseline
        simulation.set_input(BENEFIT, year, values(source, BENEFIT, year) + 1_000)
    return simulation


def benchmark(years=(YEAR,), *, claim=True, reform=None, cls=Simulation):
    baseline = Simulation(situation=family(years))
    amounts = {
        str(year): (
            baseline.tax_benefit_system.parameters.get_child(ELDEST)(str(year))
            + 1_000 / 52
            if claim
            else 0
        )
        for year in years
    }
    return cls(situation=family(years), reform={**(reform or {}), ELDEST: amounts})


@pytest.mark.parametrize("cls", [Simulation, Microsimulation])
@pytest.mark.parametrize("read_first", [False, True], ids=["baseline-set", "read-set"])
@pytest.mark.parametrize("first", [RESPONSE, "household_net_income"])
def test_direct_callback_response_matches_parameter_benchmark(cls, read_first, first):
    simulation = cls(situation=family(), reform=ELASTICITIES)
    baseline_names = simulation.baseline.input_variables
    original_names = list(baseline_names)
    baseline_net = values(simulation.baseline, "household_net_income")
    values(simulation, first)
    # This is precisely the post-construction callback route, without Scenario.
    add_benefit(simulation, read_first=read_first)
    expected = benchmark(reform=ELASTICITIES, cls=cls)
    assert values(expected, RESPONSE)[0] < 0
    for reset in (False, True):
        if reset:
            simulation.reset_calculations()
        for variable in (
            BENEFIT, "household_net_income", "relative_income_change",
            "relative_wage_change", "marginal_tax_rate", RESPONSE,
            "income_elasticity_lsr", "substitution_elasticity_lsr",
        ):
            np.testing.assert_allclose(
                values(simulation, variable), values(expected, variable),
                atol=0.01, rtol=1e-5, err_msg=variable,
            )
        np.testing.assert_allclose(values(simulation, "relative_wage_change"), 0, atol=1e-5)
        np.testing.assert_allclose(values(simulation, "substitution_elasticity_lsr"), 0, atol=0.01)
    assert simulation.baseline.input_variables is baseline_names
    assert baseline_names == original_names
    np.testing.assert_array_equal(values(simulation.baseline, "household_net_income"), baseline_net)


@pytest.mark.parametrize("claim", [True, False], ids=["formula-override", "input-only"])
def test_direct_writes_survive_reset_marginal_rates_and_export(claim):
    years = (YEAR, YEAR + 1)
    situation = family(years)
    original = copy.deepcopy(situation)
    simulation = Simulation(situation=situation)
    variable = BENEFIT if claim else CLAIM
    assert variable not in simulation.input_variables
    values(simulation, "household_net_income")
    if claim:
        add_benefit(simulation, years=years)
    else:
        for year in years:
            simulation.set_input(CLAIM, year, [False])
    expected = benchmark(years, claim=claim)
    for year in years:
        for output in (*RATES, BENEFIT, "household_net_income"):
            np.testing.assert_allclose(
                values(simulation, output, year), values(expected, output, year),
                atol=0.01, rtol=1e-5, err_msg=output,
            )
    simulation.reset_calculations()
    for year in years:
        np.testing.assert_allclose(values(simulation, BENEFIT, year), values(expected, BENEFIT, year), atol=0.01)
    frame = simulation.to_input_dataframe()
    assert all(f"{variable}__{year}" in frame for year in years)
    assert not any(column.startswith("household_net_income__") for column in frame)
    rebuilt = Simulation(dataset=frame)
    for year in years:
        np.testing.assert_allclose(values(rebuilt, BENEFIT, year), values(expected, BENEFIT, year), atol=0.01)
    assert variable not in simulation.baseline.input_variables
    assert situation == original


@pytest.mark.parametrize("claim", [True, False], ids=["formula-override", "input-only"])
def test_direct_writes_survive_obr_dynamics(claim):
    reform = {"gov.dynamic.obr_labour_supply_assumptions": {str(YEAR): True}}
    simulation = Microsimulation(situation=family(), reform=reform)
    values(simulation, "household_net_income")
    if claim:
        add_benefit(simulation)
    else:
        simulation.set_input(CLAIM, YEAR, [False])
    expected = benchmark(claim=claim, reform=reform, cls=Microsimulation)
    result = simulation.apply_dynamics(YEAR).progression
    comparison = expected.apply_dynamics(YEAR).progression
    np.testing.assert_allclose(values(simulation, BENEFIT), values(expected, BENEFIT), atol=0.01)
    for variable in ("deriv_scenario", "substitution_response", "income_response", "total_response"):
        np.testing.assert_allclose(result[variable], comparison[variable], atol=0.01, rtol=1e-5)
    assert np.any(np.asarray(comparison["income_response"]) != 0)


def test_direct_fixed_capital_gains_tax_has_zero_marginal_rate():
    simulation = Simulation(situation=family())
    assert values(simulation, RATES[2])[0] > 0
    simulation.set_input("capital_gains_tax", YEAR, [5_000, 0])
    np.testing.assert_array_equal(values(simulation, RATES[2]), [0, 0])
    simulation.reset_calculations()
    np.testing.assert_array_equal(values(simulation, "capital_gains_tax"), [5_000, 0])


@pytest.mark.parametrize("route", ["calculated", "deleted", "clone", "other-branch"])
def test_direct_retention_excludes_calculated_deleted_and_foreign_inputs(route):
    simulation = Simulation(situation=family())
    original = list(simulation.input_variables)
    if route == "calculated":
        values(simulation, "household_net_income")
    elif route == "deleted":
        simulation.set_input(BENEFIT, YEAR, [0])
        simulation.delete_arrays(BENEFIT, YEAR)
    elif route == "clone":
        simulation.clone().set_input(BENEFIT, YEAR, [0])
    else:
        simulation.get_branch("owned-by-user").set_input(BENEFIT, YEAR, [0])
    simulation.reset_calculations()
    assert simulation.input_variables == original
    np.testing.assert_array_equal(values(simulation, BENEFIT), values(simulation.baseline, BENEFIT))


def test_direct_zero_overwrite_and_inherited_branch_are_isolated():
    situation = family()
    situation["benunits"]["family"][BENEFIT] = {YEAR: 500}
    simulation = Simulation(situation=situation)
    simulation.set_input(BENEFIT, YEAR, [0])
    branch = simulation.get_branch("owned-by-user")
    branch.reset_calculations()
    np.testing.assert_array_equal(values(branch, BENEFIT), [0])
    simulation.reset_calculations()
    np.testing.assert_array_equal(values(simulation, BENEFIT), [0])
    np.testing.assert_array_equal(values(simulation.baseline, BENEFIT), [500])
    assert simulation.branches["owned-by-user"] is branch


def test_shipped_pip_callback_retains_its_explicit_periods():
    years = tuple(range(2025, 2030))
    people = {
        f"person{i}": {
            "age": {year: 30 for year in years},
            "pip_dl": {year: 100 for year in years},
            "pip_m": {year: 0 for year in years},
        }
        for i in range(8)
    }
    simulation = Simulation(situation={
        "people": people,
        "benunits": {name: {"members": [name]} for name in people},
        "households": {name: {"members": [name]} for name in people},
    })
    phase_in_pip(simulation)
    expected = {year: values(simulation, "pip", year) for year in years}
    assert np.any(expected[2029] == 0) and np.any(expected[2029] > 0)
    simulation.reset_calculations()
    for year in years:
        np.testing.assert_array_equal(values(simulation, "pip", year), expected[year])
        np.testing.assert_array_equal(values(simulation.baseline, "pip", year), np.full(8, 100))
    frame = simulation.to_input_dataframe()
    assert all(f"pip__{year}" in frame for year in years)
