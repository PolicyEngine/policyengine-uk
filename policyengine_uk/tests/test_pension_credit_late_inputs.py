"""Explicit tax reliefs survive Pension Credit's earnings counterfactuals."""

from copy import deepcopy

import numpy as np
import pytest

from policyengine_uk import Simulation


@pytest.mark.parametrize("late", [False, True])
def test_explicit_allowances_keep_couple_award_flat(late):
    # Two AA recipients qualify for the £20/week combined disregard.
    # The explicit £20,000 allowance leaves £148 pension tax after marriage
    # allowance; £1,000 wages adds £200 tax and £800 net earnings, all ignored.
    # PC income therefore stays £22,000 - £148 = £21,852, and PC £5,986.20.
    situation = {
        "people": {
            "a": {
                "age": {"2026": 70},
                "private_pension_income": {"2026": 22_000},
                "attendance_allowance": {"2026": 3_000},
            },
            "b": {"age": {"2026": 70}, "attendance_allowance": {"2026": 3_000}},
        },
        "benunits": {"b": {"members": ["a", "b"], "would_claim_pc": {"2026": True}}},
        "households": {"h": {"members": ["a", "b"]}},
    }
    awards = []
    for wages, expected_tax, expected_disregard in [(0, 0, 0), (1_000, 200, 800)]:
        data = deepcopy(situation)
        data["people"]["a"]["employment_income"] = {"2026": wages}
        if not late:
            for name, allowance in [("a", 20_000), ("b", 12_570)]:
                data["people"][name]["personal_allowance"] = {"2026": allowance}
        sim = Simulation(situation=data)
        if late:
            sim.set_input("personal_allowance", 2026, [20_000, 12_570])
        assert sim.calculate("is_pension_credit_eligible", 2026)[0]
        assert sim.calculate("pension_credit_employment_income_tax", 2026)[
            0
        ] == pytest.approx(expected_tax)
        assert sim.calculate("pension_credit_earnings_disregard", 2026)[
            0
        ] == pytest.approx(expected_disregard)
        assert sim.calculate("pension_credit_income", 2026)[0] == pytest.approx(21_852)
        awards.append(sim.calculate("pension_credit", 2026)[0])
        np.testing.assert_array_equal(
            sim.calculate("personal_allowance", 2026), [20_000, 12_570]
        )
        assert sim.branches == {}
    assert awards == pytest.approx([5_986.20, 5_986.20], abs=0.01)


def test_late_single_person_allowance_survives_counterfactual():
    # £18,000 pension is below the explicit £20,000 allowance. With £10,000
    # wages, £8,000 is taxed at 20%: the entire £1,600 is caused by employment.
    sim = Simulation(
        situation={
            "people": {
                "a": {
                    "age": {"2026": 75},
                    "private_pension_income": {"2026": 18_000},
                    "employment_income": {"2026": 10_000},
                }
            },
            "benunits": {"b": {"members": ["a"]}},
            "households": {"h": {"members": ["a"], "country": {"2026": "ENGLAND"}}},
        }
    )
    sim.set_input("personal_allowance", 2026, [20_000])
    assert sim.calculate("income_tax", 2026)[0] == pytest.approx(1_600)
    assert (
        sim.calculate("pension_credit_income_tax_without_employment_income", 2026)[0]
        == 0
    )
    assert sim.calculate("pension_credit_employment_income_tax", 2026)[
        0
    ] == pytest.approx(1_600)
    np.testing.assert_array_equal(sim.calculate("personal_allowance", 2026), [20_000])
    assert sim.branches == {}
