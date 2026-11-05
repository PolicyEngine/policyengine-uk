"""Pension Credit receipt for UC non-dependants stays acyclic and current."""

import numpy as np
import pytest

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2025


def mixed_families():
    people = {}
    for name, age, head, wtc, pension in [
        ("tenant", 40, True, 2_000, 0),
        ("pc_older", 72, False, 2_000, 12_000),
        ("pc_younger", 40, False, 0, 0),
        ("working_non_dep", 30, False, 0, 0),
        ("renter_older", 72, True, 2_000, 0),
        ("renter_younger", 40, False, 0, 0),
    ]:
        people[name] = {
            "age": {YEAR: age},
            "is_household_head": {YEAR: head},
            "is_claimant_or_partner": {YEAR: True},
            "working_tax_credit_reported": {YEAR: wtc},
            "state_pension_reported": {YEAR: pension},
            "employment_income": {YEAR: 0},
        }
    benunits = {}
    for name, members, saving, claims in [
        ("tenant", ["tenant"], False, True),
        ("pc_non_deps", ["pc_older", "pc_younger"], True, True),
        ("working_non_dep", ["working_non_dep"], False, False),
        ("protected_renters", ["renter_older", "renter_younger"], True, True),
    ]:
        benunits[name] = {
            "members": members,
            "has_mixed_age_couple_pension_credit_saving": {YEAR: saving},
            "would_claim_uc": {YEAR: False},
            "would_claim_uc_at_legacy_closure": {YEAR: claims},
        }
    households = {
        "with_non_deps": {
            "members": ["tenant", "pc_older", "pc_younger", "working_non_dep"],
            "rent": {YEAR: 9_000},
            "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
        },
        "protected_renters": {
            "members": ["renter_older", "renter_younger"],
            "rent": {YEAR: 9_000},
            "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
        },
    }
    return {"people": people, "benunits": benunits, "households": households}


def test_non_dependants_pension_credit_exempts_only_its_own_family():
    sim = Simulation(situation=mixed_families())
    # Calculate UC first: the renters' UC must not ask for their own PC
    # through the non-dependant exemption and recurse into UC entitlement.
    uc = np.asarray(sim.calculate("universal_credit", YEAR))
    pc = np.asarray(sim.calculate("pension_credit", YEAR))
    np.testing.assert_array_equal(
        sim.calculate("uc_non_dep_receives_pension_credit", YEAR),
        [False, True, False, False],
    )
    assert pc[1] > 0
    assert uc[1] == 0
    assert uc[0] > 0 and uc[3] > 0
    assert pc[0] == 0 and pc[3] == 0
    # Both members of the protected PC family are exempt. Only the separate
    # working-age non-dependant contributes 12 x 93.02 in 2025-26.
    np.testing.assert_allclose(
        sim.calculate("uc_non_dep_deductions", YEAR),
        [1_116.24, 0, 0, 0],
        atol=0.01,
    )


def test_non_dependant_exemption_recalculates_after_earnings_change():
    sim = Simulation(situation=mixed_families())
    assert sim.calculate("uc_non_dep_receives_pension_credit", YEAR)[1]
    sim.set_input("employment_income", YEAR, [0, 50_000, 0, 0, 0, 0])
    sim.drop_computed_arrays()
    assert sim.calculate("pension_credit", YEAR)[1] == 0
    assert not sim.calculate("uc_non_dep_receives_pension_credit", YEAR)[1]
    # The two former PC recipients now contribute alongside the other
    # non-dependant. A stale counterfactual branch would keep them exempt.
    np.testing.assert_allclose(
        sim.calculate("uc_non_dep_deductions", YEAR),
        [3_348.72, 0, 0, 0],
        atol=0.01,
    )


def test_non_dependant_exemption_keeps_frozen_pension_credit_receipt():
    remove_couple_guarantee = {
        "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.COUPLE": {
            "2025-01-01": 0
        }
    }
    unfrozen = Simulation(situation=mixed_families(), reform=remove_couple_guarantee)
    frozen = Simulation(
        situation=mixed_families(),
        reform={
            **remove_couple_guarantee,
            "gov.contrib.freeze_pension_credit": {"2025-01-01": True},
        },
    )
    assert unfrozen.calculate("pension_credit", YEAR)[1] == 0
    assert not unfrozen.calculate("uc_non_dep_receives_pension_credit", YEAR)[1]
    assert frozen.calculate("pension_credit", YEAR)[1] > 0
    assert frozen.calculate("uc_non_dep_receives_pension_credit", YEAR)[1]
