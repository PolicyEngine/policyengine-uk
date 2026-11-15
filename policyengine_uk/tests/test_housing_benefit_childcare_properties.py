"""Housing Benefit childcare invariants for independently assessed inputs.

C1: the deduction is nonnegative and no greater than either the qualifying
charge cap or the childcare earnings limit.
C2: increasing private pension or maintenance income cannot increase the
deduction when earnings, tax credits and the other assessed inputs are fixed.
C3: the limit is max(0, net earnings - applied standard - accommodation) plus
WTC and CTC, reading the applied standard from the shared model variable.
C4: increasing net earnings cannot lower the limit, and increasing childcare
charges cannot lower the deduction.

Selected standards, accommodation and tax credits are pre-assessed inputs so
these properties isolate the earnings residual. Standards, accommodation,
charges and tax credits are nonnegative; net earnings may be negative and
permitted work may be negative to exercise their zero floors. The applied
standard is always calculated by the model, never supplied as an input.
Each population contains independent benefit units with actual adult/child
members; lone-parent status is supplied consistently with those members.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st
from policyengine_core.simulations import Simulation

from policyengine_uk.system import system


YEAR = 2026
TOLERANCE = 1e-6
PROPERTY_SETTINGS = settings(
    max_examples=5,
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def _case(**overrides):
    case = {
        "net_earnings": 0,
        "selected_standard": 0,
        "permitted_work": 0,
        "lone_parent": False,
        "children": 1,
        "childcare": 1_000,
        "accommodation": 0,
        "wtc": 0,
        "ctc": 0,
        "private_pension": 0,
        "maintenance": 0,
    }
    case.update(overrides)
    return case


CASES = st.fixed_dictionaries(
    {
        "net_earnings": st.integers(-100, 40_000),
        "selected_standard": st.sampled_from([0, 260, 520, 1_040, 1_300]),
        "permitted_work": st.sampled_from([-1, 0, 1, 1_040, 1_300, 9_542]),
        "lone_parent": st.booleans(),
        "children": st.integers(0, 2),
        "childcare": st.integers(0, 25_000),
        "accommodation": st.integers(0, 10_000),
        "wtc": st.integers(0, 10_000),
        "ctc": st.integers(0, 10_000),
        "private_pension": st.integers(0, 20_000),
        "maintenance": st.integers(0, 20_000),
    }
)
POPULATIONS = st.lists(CASES, min_size=1, max_size=24)
EDGE_CASES = [
    _case(),
    _case(
        net_earnings=2_000,
        selected_standard=1_300,
        permitted_work=1,
        lone_parent=True,
        childcare=2_000,
    ),
    _case(net_earnings=-1, selected_standard=260, permitted_work=1),
    _case(
        selected_standard=1_040,
        children=2,
        childcare=25_000,
        wtc=500,
        ctc=1_000,
    ),
    _case(
        net_earnings=10_000,
        selected_standard=520,
        children=0,
        childcare=25_000,
    ),
    _case(
        net_earnings=5_000,
        selected_standard=1_040,
        lone_parent=True,
        childcare=25_000,
        accommodation=8_000,
    ),
    _case(
        net_earnings=30_000,
        selected_standard=1_040,
        children=2,
        childcare=25_000,
        wtc=1_000,
    ),
]


def _evaluate(cases):
    people = {}
    benunits = {}
    households = {}
    for index, case in enumerate(cases):
        # A unit with no children has no lone parent. Otherwise construct one
        # adult for a lone parent and two adults for a couple.
        lone_parent = case["lone_parent"] and case["children"] > 0
        members = []
        for adult_index in range(1 if lone_parent else 2):
            name = f"adult_{index}_{adult_index}"
            members.append(name)
            people[name] = {
                "age": {YEAR: 40},
                "is_claimant_or_partner": {YEAR: True},
                "is_child_or_young_person_for_legacy_benefits": {YEAR: False},
                "childcare_expenses": {
                    YEAR: case["childcare"] if adult_index == 0 else 0
                },
                "private_pension_income": {
                    YEAR: case["private_pension"] if adult_index == 0 else 0
                },
                "maintenance_income": {
                    YEAR: case["maintenance"] if adult_index == 0 else 0
                },
            }
        for child_index in range(case["children"]):
            name = f"child_{index}_{child_index}"
            members.append(name)
            people[name] = {
                "age": {YEAR: 8},
                "is_claimant_or_partner": {YEAR: False},
                "is_child_or_young_person_for_legacy_benefits": {YEAR: True},
            }
        benunits[f"benunit_{index}"] = {
            "members": members,
            "is_lone_parent": {YEAR: lone_parent},
            "housing_benefit_net_earnings": {YEAR: case["net_earnings"]},
            "housing_benefit_special_earnings_disregard": {
                YEAR: case["selected_standard"]
            },
            "housing_benefit_permitted_work_disregard": {YEAR: case["permitted_work"]},
            "housing_benefit_specified_or_temporary_accommodation_disregard": {
                YEAR: case["accommodation"]
            },
            "working_tax_credit": {YEAR: case["wtc"]},
            "child_tax_credit": {YEAR: case["ctc"]},
        }
        households[f"household_{index}"] = {"members": members}
    simulation = Simulation(
        tax_benefit_system=system,
        situation={
            "people": people,
            "benunits": benunits,
            "households": households,
        },
    )
    result = {
        "limit": simulation.calculate("housing_benefit_childcare_earnings_limit", YEAR),
        "deduction": simulation.calculate(
            "housing_benefit_applicable_income_childcare_element", YEAR
        ),
        "standard": simulation.calculate(
            "housing_benefit_applied_standard_earnings_disregard", YEAR
        ),
        "count": simulation.calculate(
            "num_relevant_children_for_housing_benefit_childcare", YEAR
        ),
    }
    # The statutory charge ceiling is independent of the earnings formula.
    charge_caps = np.where(
        result["count"] > 1,
        300 * 52,
        np.where(result["count"] == 1, 175 * 52, 0),
    )
    result["capped_charge"] = np.minimum(
        np.array([case["childcare"] for case in cases]), charge_caps
    )
    return result


@PROPERTY_SETTINGS
@given(cases=POPULATIONS)
@example(cases=EDGE_CASES)
def test_c1_childcare_deduction_bounds(cases):
    result = _evaluate(cases)
    assert np.all(result["deduction"] >= -TOLERANCE)
    assert np.all(
        result["deduction"]
        <= np.minimum(result["capped_charge"], result["limit"]) + TOLERANCE
    )


@PROPERTY_SETTINGS
@given(
    cases=POPULATIONS,
    increase=st.integers(1, 20_000),
    income_kind=st.sampled_from(["private_pension", "maintenance"]),
)
@example(cases=EDGE_CASES, increase=1_000, income_kind="private_pension")
@example(cases=EDGE_CASES, increase=1_000, income_kind="maintenance")
def test_c2_unrelated_income_cannot_fund_childcare(cases, increase, income_kind):
    baseline = _evaluate(cases)
    increased = _evaluate(
        [
            {
                **case,
                income_kind: case[income_kind] + increase,
            }
            for case in cases
        ]
    )
    assert np.all(increased["deduction"] <= baseline["deduction"] + TOLERANCE)


@PROPERTY_SETTINGS
@given(cases=POPULATIONS)
@example(cases=EDGE_CASES)
def test_c3_childcare_earnings_residual_identity(cases):
    result = _evaluate(cases)
    expected = (
        np.maximum(
            0,
            np.array([case["net_earnings"] for case in cases])
            - result["standard"]
            - np.array([case["accommodation"] for case in cases]),
        )
        + np.array([case["wtc"] for case in cases])
        + np.array([case["ctc"] for case in cases])
    )
    np.testing.assert_allclose(result["limit"], expected, rtol=0, atol=TOLERANCE)


@PROPERTY_SETTINGS
@given(cases=POPULATIONS, increase=st.integers(1, 40_000))
@example(cases=EDGE_CASES, increase=1_000)
def test_c4_net_earnings_cannot_lower_childcare_limit(cases, increase):
    baseline = _evaluate(cases)
    increased = _evaluate(
        [
            {
                **case,
                "net_earnings": min(40_000, case["net_earnings"] + increase),
            }
            for case in cases
        ]
    )
    assert np.all(increased["limit"] + TOLERANCE >= baseline["limit"])


@PROPERTY_SETTINGS
@given(cases=POPULATIONS, increase=st.integers(1, 25_000))
@example(cases=EDGE_CASES, increase=1_000)
def test_c4_charges_cannot_lower_childcare_deduction(cases, increase):
    baseline = _evaluate(cases)
    increased = _evaluate(
        [
            {**case, "childcare": min(25_000, case["childcare"] + increase)}
            for case in cases
        ]
    )
    assert np.all(increased["deduction"] + TOLERANCE >= baseline["deduction"])
