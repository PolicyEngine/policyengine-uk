"""Savings Credit shares Pension Credit eligibility, not just its local age test.

The literal amounts use the existing 2026 model rates. The mixed-age case's
old positive amount is an off-route diagnostic, not lawful entitlement. The
positive controls reached pensionable age before April 2016; no protected
mixed-age Savings Credit continuity is inferred from reported Pension Credit.
"""

from copy import deepcopy

from hypothesis import example, given, settings
from hypothesis import strategies as st
import numpy as np
import pytest

from policyengine_uk import Simulation
from policyengine_uk.variables.gov.dwp.pension_credit.savings_credit.savings_credit import (
    savings_credit,
)

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
YEAR = 2026


def situation():
    units = [
        ([(80, 20_000, 0), (60, 0, 0)], 6_240),
        ([(80, 9_000, 0), (78, 9_000, 0)], 6_240),
        ([(80, 11_000, 2_000)], 7_800),
        ([(40, 0, 0)], 6_240),
    ]
    people, benunits, households = {}, {}, {}
    for i, (adults, rent) in enumerate(units):
        names = []
        for j, (age, pension, private_pension) in enumerate(adults):
            name = f"p{i}_{j}"
            names.append(name)
            people[name] = {
                "age": {YEAR: age},
                "is_claimant_or_partner": {YEAR: True},
                "state_pension": {YEAR: pension},
                "private_pension_income": {YEAR: private_pension},
            }
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_pc": {YEAR: True},
            "would_claim_housing_benefit": {YEAR: True},
            "would_claim_uc": {YEAR: False},
        }
        households[f"h{i}"] = {
            "members": names,
            "country": {YEAR: "ENGLAND"},
            "local_authority": {YEAR: "MAIDSTONE"},
            "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
            "rent": {YEAR: rent},
            "council_tax": {YEAR: 2_000},
            "savings": {YEAR: 0},
        }
    return {"people": people, "benunits": benunits, "households": households}


def ungated_simulation(data=None):
    """Retain the former amount formula for a downstream differential control."""
    sim = Simulation(situation=situation() if data is None else data)
    sim.tax_benefit_system.update_variable(
        type("savings_credit", (savings_credit,), {"defined_for": None})
    )
    return sim


@pytest.mark.parametrize("first", ["savings_credit", "pension_credit"])
def test_unprotected_mixed_age_savings_credit_is_zero(first):
    sim = Simulation(situation=situation())
    sim.calculate(first, YEAR)
    # The older member meets the local pre-2016 age condition, but the
    # unprotected younger partner excludes the couple from Pension Credit.
    assert sim.calculate("is_savings_credit_eligible", YEAR).tolist() == [
        True,
        True,
        True,
        False,
    ]
    assert sim.calculate("is_pension_credit_eligible", YEAR).tolist() == [
        False,
        True,
        True,
        False,
    ]
    # Couple: 0.6 * (18,000 - 329.75*52) = 511.80.
    # Single: 0.6*(238-208.07)*52 - 0.4*(12,914-238*52) = 718.616.
    np.testing.assert_allclose(
        sim.calculate("savings_credit", YEAR),
        [0, 511.80, 718.616, 0],
        atol=0.01,
        rtol=0,
    )


def test_shared_gate_preserves_final_pension_credit_and_consumers():
    fixed = Simulation(situation=situation())
    former = ungated_simulation()
    # The old off-route calculation was 0.6*(18,766-329.75*52) = 971.40, with the default married
    # couple receiving the existing Marriage Allowance of 1,260.
    assert former.calculate("savings_credit", YEAR)[0] == pytest.approx(
        971.40, abs=0.01
    )
    assert fixed.calculate("savings_credit", YEAR)[0] == 0
    consumers = [
        "guarantee_credit",
        "pension_credit_entitlement",
        "pension_credit",
        "in_receipt_of_savings_credit_only",
        "housing_benefit_applicable_income",
        "housing_benefit_assessable_capital",
        "housing_benefit_tariff_income",
        "housing_benefit",
        "council_tax_reduction_applicable_income",
        "council_tax_reduction_assessable_capital",
        "council_tax_reduction",
        "targeted_childcare_entitlement",
    ]
    for variable in consumers:
        np.testing.assert_allclose(
            fixed.calculate(variable, YEAR),
            former.calculate(variable, YEAR),
            atol=0.01,
            rtol=0,
            err_msg=variable,
        )
    # Both-old couple: Guarantee Credit 18,889-18,000 = 889, plus 511.80.
    for variable in ("pension_credit_entitlement", "pension_credit"):
        np.testing.assert_allclose(
            fixed.calculate(variable, YEAR),
            [0, 1_400.80, 718.616, 0],
            atol=0.01,
            rtol=0,
        )
    # The couple gets full rent on Guarantee Credit. The single's HB is
    # 7,800 - 0.65*(12,914+718.616-256*52) = 7,591.5996.
    np.testing.assert_allclose(
        fixed.calculate("housing_benefit", YEAR),
        [0, 6_240, 7_591.5996, 0],
        atol=0.01,
        rtol=0,
    )


def test_direct_savings_credit_input_keeps_its_existing_override_behavior():
    data = situation()
    data["benunits"]["b0"]["savings_credit"] = {YEAR: 123}
    sim = Simulation(situation=data)
    assert sim.calculate("savings_credit", YEAR)[0] == 123
    # An explicitly supplied component does not create a Pension Credit award.
    assert sim.calculate("pension_credit_entitlement", YEAR)[0] == 0
    assert sim.calculate("pension_credit", YEAR)[0] == 0
    assert sim.calculate("housing_benefit", YEAR)[0] == 0


# These are baseline input-contract invariants, not a proof of lawful historical
# Savings Credit continuity or population impacts. All components are computed;
# only the documented saving/closure scenario flags are supplied as inputs.
CONSUMER_OUTPUTS = [
    "guarantee_credit",
    "pension_credit_entitlement",
    "pension_credit",
    "in_receipt_of_savings_credit_only",
    "housing_benefit_applicable_income",
    "housing_benefit_assessable_capital",
    "housing_benefit_tariff_income",
    "housing_benefit",
    "council_tax_reduction_applicable_income",
    "council_tax_reduction_assessable_capital",
    "council_tax_reduction",
    "targeted_childcare_entitlement",
]


def _control_unit(*, protected=False, closed=False, claim=False, both_old=False):
    return {
        "adults": [
            (80, 9_000 if both_old else (0 if closed else 20_000), 0, 0),
            (78 if both_old else 60, 9_000 if both_old else 0, 0, 0),
        ],
        "protected": protected,
        "closed": closed,
        "claim_at_closure": claim,
        "claim_pc": True,
        "claim_uc": False,
        "rent": 6_240,
        "capital": 0,
        "expected_left": protected and closed and claim,
    }


@st.composite
def _unit_cases(draw):
    shape = draw(st.sampled_from(["mixed", "both_old", "working"]))
    ages = {
        "mixed": (draw(st.integers(80, 90)), draw(st.integers(25, 60))),
        "both_old": (draw(st.integers(80, 90)), draw(st.integers(80, 90))),
        "working": (draw(st.integers(25, 60)), draw(st.integers(25, 60))),
    }[shape]
    return {
        "adults": [
            (
                age,
                draw(st.integers(0, 25_000)) if age >= 80 else 0,
                draw(st.integers(0, 30_000)),
                draw(st.integers(0, 10_000)),
            )
            for age in ages
        ],
        "protected": draw(st.booleans()),
        "closed": draw(st.booleans()),
        "claim_at_closure": draw(st.booleans()),
        "claim_pc": draw(st.booleans()),
        "claim_uc": draw(st.booleans()),
        "rent": draw(st.integers(0, 12_000)),
        "capital": draw(st.integers(0, 20_000)),
    }


def _generated_situation(units):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        members = []
        for j, (age, pension, earnings, private_pension) in enumerate(unit["adults"]):
            name = f"person{i}_{j}"
            members.append(name)
            people[name] = {
                "age": {YEAR: age},
                "is_claimant_or_partner": {YEAR: True},
                "state_pension": {YEAR: pension},
                "employment_income": {YEAR: earnings},
                "private_pension_income": {YEAR: private_pension},
            }
        benunits[f"b{i}"] = {
            "members": members,
            "has_mixed_age_couple_pension_credit_saving": {YEAR: unit["protected"]},
            "legacy_benefits_closed": {YEAR: unit["closed"]},
            "would_claim_uc_at_legacy_closure": {YEAR: unit["claim_at_closure"]},
            "would_claim_pc": {YEAR: unit["claim_pc"]},
            "would_claim_uc": {YEAR: unit["claim_uc"]},
            "would_claim_housing_benefit": {YEAR: True},
        }
        households[f"h{i}"] = {
            "members": members,
            "country": {YEAR: "ENGLAND"},
            "local_authority": {YEAR: "MAIDSTONE"},
            "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
            "rent": {YEAR: unit["rent"]},
            "council_tax": {YEAR: 2_000},
            "savings": {YEAR: unit["capital"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def _assert_computed_component_invariants(sim):
    # SPCA 2002 ss.1(2)-(4), 3 and 4(1A): shared entitlement qualifies the
    # computed component. An explicit saving flag selects the existing route;
    # it does not prove the separate pre-2016 Savings Credit history.
    amount = sim.calculate("savings_credit", YEAR)
    eligible = sim.calculate("is_pension_credit_eligible", YEAR)
    assert np.all((amount <= 0) | eligible), (
        "positive computed SC requires shared eligibility"
    )
    np.testing.assert_allclose(
        sim.calculate("pension_credit_entitlement", YEAR),
        sim.calculate("guarantee_credit", YEAR) + amount,
        atol=0.01,
        rtol=0,
    )


@settings(max_examples=25, derandomize=True, database=None, deadline=None)
@given(units=st.lists(_unit_cases(), min_size=1, max_size=6))
@example(units=[_control_unit()])
@example(units=[_control_unit(protected=True)])
@example(units=[_control_unit(both_old=True)])
@example(units=[_control_unit(protected=True, closed=True, claim=True)])
def test_savings_credit_generated_invariants(units):
    data = _generated_situation(units)
    fixed = Simulation(situation=deepcopy(data))
    former = ungated_simulation(deepcopy(data))
    _assert_computed_component_invariants(fixed)
    for i, unit in enumerate(units):
        if "expected_left" in unit:
            assert (
                bool(fixed.calculate("left_pension_route_at_legacy_closure", YEAR)[i])
                == unit["expected_left"]
            )
    # Deliberately exclude raw Savings Credit: its unprotected off-route amount
    # is precisely the value the shared gate changes. Consumers keep their gates.
    for variable in CONSUMER_OUTPUTS:
        np.testing.assert_allclose(
            fixed.calculate(variable, YEAR),
            former.calculate(variable, YEAR),
            atol=0.01,
            rtol=0,
            err_msg=variable,
        )


def test_ungated_counterexample_detects_positive_component_without_entitlement():
    data = _generated_situation([_control_unit()])
    fixed = Simulation(situation=deepcopy(data))
    former = ungated_simulation(deepcopy(data))
    _assert_computed_component_invariants(fixed)
    assert former.calculate("savings_credit", YEAR)[0] > 0
    assert not former.calculate("is_pension_credit_eligible", YEAR)[0]
    # This negative control proves the invariant would detect losing the gate.
    # Current main already has the gate; this is not a claimed production RED.
    with pytest.raises(
        AssertionError, match="positive computed SC requires shared eligibility"
    ):
        _assert_computed_component_invariants(former)
