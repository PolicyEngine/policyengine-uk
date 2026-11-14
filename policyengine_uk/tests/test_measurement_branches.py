"""A measurement branch measures from inputs alone.

A branch starts from every value its simulation holds. A measurement branch
drops what the simulation calculated, so a result the simulation calculated
with a behavioural response is recalculated without it, at the branch's
inputs, rather than read from the simulation.
"""

import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.model_api import Scenario
from policyengine_uk.utils.measurement_branches import (
    BEHAVIOURAL_RESPONSES,
    held_behavioural_responses,
    hold_behavioural_responses,
    measurement_branch,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025
ELASTICITIES = {
    "gov.simulation.labour_supply_responses.substitution_elasticity": {str(YEAR): 0.25},
    "gov.simulation.labour_supply_responses.income_elasticity": {str(YEAR): -0.05},
}
BASIC_RATE_RISE = {"gov.hmrc.income_tax.rates.uk[0].rate": {str(YEAR): 0.30}}
STATIC_CAPITAL_GAINS = {
    "gov.simulation.capital_gains_responses.elasticity": {str(YEAR): 0},
    "gov.simulation.capital_gains_responses.mtr_elasticity": {str(YEAR): 0},
}
SITUATION = {
    "people": {"person": {"age": {YEAR: 45}, "employment_income": {YEAR: 40_000}}},
    "benunits": {"benunit": {"members": ["person"]}},
    "households": {"household": {"members": ["person"]}},
}


def value(simulation, variable):
    return float(np.asarray(simulation.calculate(variable, YEAR), dtype=float)[0])


def test_a_measurement_branch_drops_what_its_simulation_calculated():
    reform = {**BASIC_RATE_RISE, **STATIC_CAPITAL_GAINS}
    responding = Simulation(
        situation=SITUATION,
        scenario=Scenario(parameter_changes={**reform, **ELASTICITIES}),
    )
    assert value(responding, "employment_income_behavioral_response") < 0
    with_response = value(responding, "household_net_income")

    branch = measurement_branch(responding, "probe", YEAR, {})

    without_response = Simulation(
        situation=SITUATION, scenario=Scenario(parameter_changes=reform)
    )
    measured = value(branch, "household_net_income")
    assert measured == value(without_response, "household_net_income")
    assert measured != with_response
    # The branch is not kept, and the simulation's own results are untouched.
    assert "probe" not in responding.branches
    assert value(responding, "household_net_income") == with_response


def test_a_branch_with_its_parents_rules_takes_the_parents_response(monkeypatch):
    """The Pension Credit branch of the UC non-dependant exemption fixes the
    UC housing element at zero. It changes inputs, not policy, so it takes the
    simulation's labour supply response instead of measuring the whole
    population again with that element held on the reform's side only."""
    from policyengine_uk.utils import labour_supply_responses

    measured_from = []
    measure = labour_supply_responses.measurement_branch

    def recording(simulation, name, period, inputs):
        if name == "lsr_measurement":
            measured_from.append(simulation.branch_name)
        return measure(simulation, name, period, inputs)

    monkeypatch.setattr(labour_supply_responses, "measurement_branch", recording)
    members = ["earner", "partner", "older_child", "younger_child"]
    renting_family = {
        "people": {
            "earner": {"age": {YEAR: 35}, "employment_income": {YEAR: 22_000}},
            "partner": {"age": {YEAR: 33}},
            "older_child": {"age": {YEAR: 6}},
            "younger_child": {"age": {YEAR: 3}},
        },
        "benunits": {"benunit": {"members": members}},
        "households": {
            "household": {
                "members": members,
                "rent": {YEAR: 10_800},
                "tenure_type": {YEAR: "RENT_PRIVATELY"},
            }
        },
    }
    responding = Simulation(
        situation=renting_family,
        scenario=Scenario(
            parameter_changes={
                **BASIC_RATE_RISE,
                **STATIC_CAPITAL_GAINS,
                **ELASTICITIES,
            }
        ),
    )

    assert value(responding, "universal_credit") > 0
    responding.calculate("household_net_income", YEAR)

    assert value(responding, "employment_income_behavioral_response") < 0
    assert measured_from == ["default"]


@pytest.mark.parametrize(
    "elasticities, terms_measured",
    [
        ({}, []),
        # Only the income term is nonzero, so only it reads the measurement.
        (
            {
                "gov.simulation.labour_supply_responses.income_elasticity": {
                    str(YEAR): -0.05
                }
            },
            ["relative_income_change"],
        ),
    ],
)
def test_a_term_with_a_zero_elasticity_measures_nothing(
    monkeypatch, elasticities, terms_measured
):
    """policyengine.py asks for both terms on every UK simulation. A term
    whose elasticity is zero is zero, so it measures nothing."""
    from policyengine_uk.utils import labour_supply_responses

    opened = []
    measure = labour_supply_responses.measurement_branch

    def recording(simulation, name, period, inputs):
        opened.append(name)
        return measure(simulation, name, period, inputs)

    monkeypatch.setattr(labour_supply_responses, "measurement_branch", recording)
    simulation = Simulation(
        situation=SITUATION,
        scenario=Scenario(
            parameter_changes={
                **BASIC_RATE_RISE,
                **STATIC_CAPITAL_GAINS,
                **elasticities,
            }
        ),
    )

    terms = {
        "income_elasticity_lsr": "relative_income_change",
        "substitution_elasticity_lsr": "relative_wage_change",
    }
    # The terms require the response first (policyengine-core 3.32 enforces
    # it). With no elasticities the response returns early, but the terms are
    # still asked for afterwards.
    simulation.calculate("employment_income_behavioral_response", YEAR)
    for term in terms:
        simulation.calculate(term, YEAR)
    calculated = {
        change
        for term, change in terms.items()
        if simulation.get_holder(change).get_known_periods()
    }

    assert sorted(calculated) == terms_measured
    if not terms_measured:
        assert opened == []


def test_holding_the_responses_keeps_a_branch_from_measuring_them_again(monkeypatch):
    """The marginal rate variables hold every response in the branches where
    they step an input. A branch that shares the simulation's rules would take
    the labour supply response through response_source anyway, so this uses a
    branch with its own copy of the rules, which isolates the hold: emptied as
    the marginal rate variables empty theirs, it measures the response again
    unless the responses are held."""
    from policyengine_uk.utils import labour_supply_responses

    measured_from = []
    measure = labour_supply_responses.measurement_branch

    def recording(simulation, name, period, inputs):
        if name == "lsr_measurement":
            measured_from.append(simulation.branch_name)
        return measure(simulation, name, period, inputs)

    monkeypatch.setattr(labour_supply_responses, "measurement_branch", recording)
    responding = Simulation(
        situation=SITUATION,
        scenario=Scenario(
            parameter_changes={
                **BASIC_RATE_RISE,
                **STATIC_CAPITAL_GAINS,
                **ELASTICITIES,
            }
        ),
    )
    response = value(responding, "employment_income_behavioral_response")
    held = held_behavioural_responses(responding.person, YEAR)
    assert set(held) == set(BEHAVIOURAL_RESPONSES)

    def emptied_branch(name):
        branch = responding.get_branch(name, clone_system=True)
        variables = responding.tax_benefit_system.variables
        for variable, data in variables.items():
            if (
                variable not in responding.input_variables
                and not data.is_input_variable()
            ):
                branch.delete_arrays(variable)
        return branch

    measured_from.clear()
    unheld = emptied_branch("unheld")
    assert value(unheld, "employment_income_behavioral_response") == response
    assert measured_from == ["unheld"]

    measured_from.clear()
    branch = emptied_branch("held")
    hold_behavioural_responses(branch, YEAR, held)
    assert value(branch, "employment_income_behavioral_response") == response
    assert measured_from == []
