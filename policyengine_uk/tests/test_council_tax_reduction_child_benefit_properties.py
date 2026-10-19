"""Pensioner Child Benefit exclusion and unchanged adjacent CTR contracts.

These model2026 tests use actual Child Benefit claims and family incomes, not
forced applicable income, pensioner status or reduction awards. The 20% cash
relation is conditional on an interior award; the existing floor/cap still apply.
"""

from copy import deepcopy

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
COUNTRIES = {
    "ENGLAND": ("LONDON", "MAIDSTONE"),
    "SCOTLAND": ("SCOTLAND", "GLASGOW_CITY"),
    "WALES": ("WALES", "CARDIFF"),
}


def family(country="ENGLAND", pension=16000, age=70, children=1, council_tax=4000):
    region, authority = COUNTRIES.get(country, ("NORTHERN_IRELAND", "BELFAST"))
    people = {"parent": {"age": {YEAR: age}, "is_parent": {YEAR: True}}}
    people["parent"][
        "state_pension" if age >= 67 else "employment_income_before_lsr"
    ] = {YEAR: pension}
    for index in range(children):
        people[f"child{index}"] = {"age": {YEAR: 9 + index}}
    return {
        "people": people,
        "benunits": {
            "family": {
                "members": list(people),
                "would_claim_pc": {YEAR: False},
                "would_claim_uc": {YEAR: False},
            }
        },
        "households": {
            "home": {
                "members": list(people),
                "region": {YEAR: region},
                "local_authority": {YEAR: authority},
                "tenure_type": {YEAR: "OWNED_OUTRIGHT"},
                "council_tax": {YEAR: council_tax},
                "savings": {YEAR: 0},
            }
        },
    }


def calculate(data, claim, status_first=False):
    data = deepcopy(data)
    for unit in data["benunits"].values():
        unit["would_claim_child_benefit"] = {YEAR: claim}
    sim = Simulation(situation=data)
    first = (
        "council_tax_reduction_pensioner"
        if status_first
        else "council_tax_reduction_applicable_income"
    )
    sim.calculate(first, YEAR)
    names = [
        "child_benefit",
        "council_tax_reduction_pensioner",
        "council_tax_reduction_applicable_income",
        "council_tax_reduction_applicable_amount",
        "council_tax_benefit",
        "council_tax_reduction",
        "household_net_income",
        "in_receipt_of_guarantee_credit",
        "in_receipt_of_savings_credit_only",
    ]
    return {name: np.asarray(sim.calculate(name, YEAR)) for name in names}


@settings(max_examples=4, deadline=None, derandomize=True)
@given(
    st.sampled_from(sorted(COUNTRIES)),
    st.integers(15000, 19000),
    st.integers(1, 2),
    st.booleans(),
)
def test_pensioner_ctr_is_invariant_to_actual_child_benefit_claim(
    country, pension, children, status_first
):
    data = family(country, pension, children=children)
    paid = calculate(data, True, status_first)
    unpaid = calculate(data, False, not status_first)
    assert paid["child_benefit"][0] > 0
    assert unpaid["child_benefit"][0] == 0
    assert paid["council_tax_reduction_pensioner"][0]
    assert not paid["in_receipt_of_guarantee_credit"][0]
    assert not paid["in_receipt_of_savings_credit_only"][0]
    np.testing.assert_allclose(
        paid["council_tax_reduction_applicable_income"],
        unpaid["council_tax_reduction_applicable_income"],
        atol=0.01,
        rtol=0,
    )
    np.testing.assert_allclose(
        paid["council_tax_reduction"],
        unpaid["council_tax_reduction"],
        atol=0.01,
        rtol=0,
    )
    # The payable award reaches the household consumer. No other benefit/tax
    # changes in these owner-occupier, no-PC/no-UC, below-HICBC families.
    np.testing.assert_allclose(
        paid["household_net_income"] - unpaid["household_net_income"],
        paid["child_benefit"],
        atol=0.02,
        rtol=0,
    )
    # Named old-law counterfactual: before the exclusion, an interior award
    # counted this cash and lost exactly 20% of it. The new award is not clipped.
    income = unpaid["council_tax_reduction_applicable_income"][0]
    amount = unpaid["council_tax_reduction_applicable_amount"][0]
    liability = 4000
    old_award = max(
        0, liability - 0.2 * max(0, income + paid["child_benefit"][0] - amount)
    )
    assert income > amount and old_award > 0
    assert (
        abs(
            paid["council_tax_reduction"][0]
            - old_award
            - 0.2 * paid["child_benefit"][0]
        )
        < 0.02
    )


def test_working_age_and_northern_ireland_keep_counting_child_benefit():
    for country, authority in [
        ("SCOTLAND", "GLASGOW_CITY"),
        ("WALES", "CARDIFF"),
        ("ENGLAND", "MERTON"),
        ("ENGLAND", "KINGSTON_UPON_THAMES"),
        ("ENGLAND", "NEWHAM"),
        ("ENGLAND", "WESTMINSTER"),
        ("ENGLAND", "OXFORD"),
        ("NORTHERN_IRELAND", "BELFAST"),
    ]:
        age = 70 if country == "NORTHERN_IRELAND" else 40
        data = family(country, 18000, age=age)
        data["households"]["home"]["local_authority"] = {YEAR: authority}
        paid, unpaid = calculate(data, True), calculate(data, False, True)
        assert paid["child_benefit"][0] > 0
        if age == 40:
            assert not paid["council_tax_reduction_pensioner"][0]
        np.testing.assert_allclose(
            paid["council_tax_reduction_applicable_income"]
            - unpaid["council_tax_reduction_applicable_income"],
            paid["child_benefit"],
            atol=0.02,
            rtol=0,
        )
        assert (
            paid["council_tax_reduction"][0]
            <= unpaid["council_tax_reduction"][0] + 0.01
        )
        if authority == "OXFORD":
            # Oxford already removes CB before its own band selection.
            np.testing.assert_allclose(
                paid["council_tax_reduction"],
                unpaid["council_tax_reduction"],
                atol=0.01,
                rtol=0,
            )


def test_own_family_pensioner_mask_and_query_order_ignore_outside_family():
    data = family()
    data["people"].update(
        {
            "other": {"age": {YEAR: 40}, "employment_income_before_lsr": {YEAR: 18000}},
            "other_child": {"age": {YEAR: 7}},
        }
    )
    data["benunits"]["other_family"] = {
        "members": ["other", "other_child"],
        "would_claim_pc": {YEAR: False},
        "would_claim_uc": {YEAR: False},
    }
    data["households"]["home"]["members"] += ["other", "other_child"]
    paid, unpaid = calculate(data, True), calculate(data, False, True)
    np.testing.assert_array_equal(
        paid["council_tax_reduction_pensioner"], [True, False]
    )
    delta = (
        paid["council_tax_reduction_applicable_income"]
        - unpaid["council_tax_reduction_applicable_income"]
    )
    np.testing.assert_allclose(delta, [0, paid["child_benefit"][1]], atol=0.02, rtol=0)
    reversed_data = deepcopy(data)
    reversed_data["people"] = dict(reversed(list(data["people"].items())))
    reversed_data["benunits"] = dict(reversed(list(data["benunits"].items())))
    for unit in reversed_data["benunits"].values():
        unit["members"] = list(reversed(unit["members"]))
    reverse = calculate(reversed_data, True, True)
    for name in [
        "child_benefit",
        "council_tax_reduction_pensioner",
        "council_tax_reduction_applicable_income",
        "council_tax_benefit",
    ]:
        np.testing.assert_allclose(reverse[name][::-1], paid[name], atol=0.02, rtol=0)
    np.testing.assert_allclose(
        reverse["council_tax_reduction"],
        paid["council_tax_reduction"],
        atol=0.02,
        rtol=0,
    )
