"""Property and differential tests for the benefit cap reduction reported.

``uc_benefit_cap_reduction`` is the UC Regs 2013 reg. 81 amount: the excess
of the welfare benefits over the Universal Credit cap, less the childcare
costs element, on an award only. It can exceed the award before the cap.
``uc_benefit_cap_reduction_after_floor`` is what the award actually loses.
``benefit_cap_reduction`` adds that to the Housing Benefit reduction (HB Regs
2006 reg. 75D), the amount DWP's benefit cap statistics measure, and
policyengine-uk-data calibrates against it.

``REFERENCE_TOTAL`` restores the parent commit's ``benefit_cap_reduction``,
which added the reg. 81 amount itself (verbatim ``adds``).

Properties 1-6 are checked over generated coherent benefit units and
``EXAMPLE_UNITS`` under current law and protected floors of 0.5, 0.85, 1 and
1.2. Coherent inputs have no positive pre-cap UC award without a UC claim.
The separate override regression documents behavior outside that domain.
Property 7 checks current law, with a zero protected floor:

1. Definition. ``benefit_cap_reduction`` is
   ``uc_benefit_cap_reduction_after_floor`` plus
   ``housing_benefit_benefit_cap_reduction``.
2. Bound. The UC part is between 0 and ``min(reg. 81 amount, max(award
   before the cap, 0))``, and equals it under current law. An award cannot
   be reduced below nil, and WRA 2012 s. 96(2) allows a reduction smaller
   than the excess ("an amount up to or equalling the excess").
3. Incidence, for coherent inputs. Under current law
   ``benefit_cap_reduction > 0`` exactly where the parent commit's total is
   positive, so uk-data's count of capped households cannot move for these
   inputs; under a floor it is positive only where that total is.
4. Differential. ``universal_credit``, ``uc_deductions``,
   ``uc_has_deduction``, ``housing_benefit`` and ``household_net_income``
   equal the parent commit's for every floor: nothing in the model reads the
   reported total. The parent's total is never smaller. Under current law
   the totals are equal wherever the reg. 81 amount fits in the award.
5. Conservation, for every floor. ``benefit_cap_reduction`` equals what the
   two caps take from the awards: ``max(award before the cap, 0) -
   uc_deductions - universal_credit`` plus ``housing benefit before the cap -
   housing_benefit``.
6. A protected floor never raises the reduction reported above its
   current-law amount for the same family.
7. Current-law monotonicity (zero protected floor). With the award before
   the cap fixed, the reduction reported does not fall as the welfare
   benefits rise, and does not rise as the childcare costs element rises.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_core.reforms import Reform
from policyengine_uk import Simulation
from policyengine_uk.model_api import *

PERIOD = 2025
FLOORS = [0.0, 0.5, 0.85, 1.0, 1.2]
CAPS = [14_753.0, 16_967.0, 22_020.0, 25_323.0, np.inf]
COMBINATIONS = ["ADVANCE_ONLY", "THIRD_PARTY_ONLY", "GOVERNMENT_ONLY", "ALL_THREE"]
# Float variables are float32: allow a few units in the last place at 100k.
TOL = 0.05
# Each example builds up to three simulations, and a reform clones the
# tax-benefit system (about 3.5 seconds each).
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


# ---------------------------------------------------------------------------
# The parent commit's total: the reg. 81 amount plus the Housing Benefit
# reduction (verbatim adds).


def _reference_benefit_cap_reduction():
    class benefit_cap_reduction(Variable):
        label = "benefit cap reduction (parent commit)"
        entity = BenUnit
        definition_period = YEAR
        value_type = float
        unit = GBP
        adds = ["uc_benefit_cap_reduction", "housing_benefit_benefit_cap_reduction"]

    return benefit_cap_reduction


class REFERENCE_TOTAL(Reform):
    def apply(self):
        self.update_variable(_reference_benefit_cap_reduction())


# ---------------------------------------------------------------------------
# Benefit units. Inputs are set directly at the cap's boundary: the award
# before the cap, the welfare benefits (that award plus the other capped
# benefits), the cap, the childcare costs element and the deduction inputs.

awards = st.one_of(
    st.just(0.0),
    st.floats(-3_000, -0.01),
    st.floats(0.01, 500),
    st.floats(500, 40_000),
)
amounts = st.one_of(st.just(0.0), st.floats(0, 60_000))


@st.composite
def units(draw):
    scheme = draw(st.sampled_from(["UC", "UC", "UC", "HB", "NONE"]))
    return dict(
        scheme=scheme,
        award=draw(awards),
        other_benefits=draw(amounts),
        cap=draw(st.sampled_from(CAPS)),
        childcare=draw(st.one_of(st.just(0.0), st.floats(0, 15_000))),
        latent_rate=draw(st.one_of(st.just(0.0), st.floats(0, 0.4))),
        combination=draw(st.sampled_from(COMBINATIONS)),
        # 0 falls below any incidence of deductions; 1 (the calculator
        # default) never does.
        draw=draw(st.sampled_from([0.0, 1.0])),
    )


populations = st.lists(units(), min_size=1, max_size=12)


def unit(scheme="UC", award=0.0, other_benefits=0.0, cap=22_020.0, **kw):
    values = dict(
        scheme=scheme,
        award=award,
        other_benefits=other_benefits,
        cap=cap,
        childcare=0.0,
        latent_rate=0.0,
        combination="ADVANCE_ONLY",
        draw=1.0,
    )
    values.update(kw)
    return values


def example_units():
    return [
        # UC before the cap 100, welfare benefits 30,000, cap 22,020: reg. 81
        # says 7,980, and the award can lose 100.
        unit(award=100.0, other_benefits=29_900.0),
        # The reg. 81 amount equals the award before the cap.
        unit(award=7_980.0, other_benefits=22_020.0),
        # The childcare costs element offsets part of the excess (reg. 81(1)).
        unit(award=15_000.0, other_benefits=15_000.0, childcare=3_000.0),
        # Reg. 81(2): the childcare costs element exceeds the excess.
        unit(award=15_000.0, other_benefits=15_000.0, childcare=9_000.0),
        # Deductions come after the cap, from the award it leaves.
        unit(
            award=6_000.0,
            other_benefits=21_000.0,
            latent_rate=0.25,
            combination="ADVANCE_ONLY",
            draw=0.0,
        ),
        # The cap takes the whole award, so nothing is left to deduct from.
        unit(
            award=1_000.0,
            other_benefits=30_000.0,
            latent_rate=0.25,
            combination="GOVERNMENT_ONLY",
            draw=0.0,
        ),
        # A negative award before the cap: no award, no reduction.
        unit(award=-500.0, other_benefits=30_000.0),
        # Housing Benefit: reg. 75D(2) leaves 50 pence a week.
        unit(scheme="HB", award=5_000.0, other_benefits=25_000.0),
        # Exempt from the cap (reg. 82 or 83).
        unit(award=2_000.0, other_benefits=40_000.0, cap=np.inf),
    ]


EXAMPLE_UNITS = example_units()


def situation(population, year=PERIOD):
    # Keep the generated claim and award inputs coherent: only UC claimants
    # receive a pre-cap UC award. Explicit overrides are tested separately.
    people, benunits, households = {}, {}, {}
    for i, u in enumerate(population):
        on_uc, on_hb = u["scheme"] == "UC", u["scheme"] == "HB"
        award = u["award"] if u["scheme"] != "NONE" else 0.0
        people[f"p{i}"] = {"age": {year: 30}}
        benunits[f"b{i}"] = {
            "members": [f"p{i}"],
            "would_claim_uc": {year: on_uc},
            "would_claim_housing_benefit": {year: on_hb},
            "universal_credit_pre_benefit_cap": {year: award if on_uc else 0.0},
            "housing_benefit_pre_benefit_cap": {
                year: max(award, 0.0) if on_hb else 0.0
            },
            "benefit_cap_welfare_benefits": {
                year: max(award, 0.0) + u["other_benefits"]
            },
            "uc_benefit_cap": {year: u["cap"]},
            "housing_benefit_benefit_cap": {year: u["cap"]},
            "uc_childcare_element": {year: u["childcare"] if on_uc else 0.0},
            "uc_latent_deduction_rate": {year: u["latent_rate"] if on_uc else 0.0},
            "uc_deduction_combination": {year: u["combination"]},
            "uc_deduction_random_draw": {year: u["draw"]},
        }
        households[f"h{i}"] = {"members": [f"p{i}"]}
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "universal_credit_pre_benefit_cap",
    "benefit_cap_welfare_benefits",
    "uc_benefit_cap",
    "uc_childcare_element",
    "uc_benefit_cap_reduction",
    "uc_benefit_cap_reduction_after_floor",
    "uc_deductions",
    "uc_has_deduction",
    "universal_credit",
    "housing_benefit_pre_benefit_cap",
    "housing_benefit_benefit_cap_reduction",
    "housing_benefit",
    "benefit_cap_reduction",
]
# One household per benefit unit, so household values line up with them.
HOUSEHOLD_VARIABLES = ["household_net_income"]
REFERENCE_OUTPUTS = [
    "universal_credit",
    "uc_deductions",
    "uc_has_deduction",
    "housing_benefit",
    "household_net_income",
]


def floor_reform(floor):
    return {
        "gov.dwp.universal_credit.deductions.protected_floor": {
            f"{PERIOD}-01-01.{PERIOD}-12-31": floor
        }
    }


def simulation(sit, floor, reference=False):
    # Current law needs no reform, which saves cloning the system.
    reforms = ((REFERENCE_TOTAL,) if reference else ()) + (
        (floor_reform(floor),) if floor else ()
    )
    if not reforms:
        return Simulation(situation=sit)
    return Simulation(
        situation=sit, reform=reforms[0] if len(reforms) == 1 else reforms
    )


def calculate(population, floor=0.0, reference=True):
    sit = situation(population)
    new = simulation(sit, floor)
    v = {
        name: np.asarray(new.calculate(name, PERIOD))
        for name in VARIABLES + HOUSEHOLD_VARIABLES
    }
    if reference:
        old = simulation(sit, floor, reference=True)
        for name in REFERENCE_OUTPUTS + ["benefit_cap_reduction"]:
            v[f"reference_{name}"] = np.asarray(old.calculate(name, PERIOD))
    return v


# ---------------------------------------------------------------------------
# Properties.


def check_invariants(population, floor):
    v = calculate(population, floor)
    msg = f"floor={floor} {population}"
    award = np.maximum(v["universal_credit_pre_benefit_cap"], 0)
    reg81 = v["uc_benefit_cap_reduction"]
    applied = v["uc_benefit_cap_reduction_after_floor"]
    hb_pre = v["housing_benefit_pre_benefit_cap"]
    hb_reduction = v["housing_benefit_benefit_cap_reduction"]
    total = v["benefit_cap_reduction"]
    old_total = v["reference_benefit_cap_reduction"]

    # 1. Definition.
    np.testing.assert_allclose(total, applied + hb_reduction, atol=TOL, err_msg=msg)

    # 2. Bound.
    bound = np.minimum(reg81, award)
    assert np.all(applied >= 0), msg
    assert np.all(applied <= bound + TOL), msg
    if floor == 0:
        np.testing.assert_allclose(applied, bound, atol=TOL, err_msg=msg)

    # 3. Incidence.
    if floor == 0:
        np.testing.assert_array_equal(total > 0, old_total > 0, err_msg=msg)
    else:
        assert np.all(~(total > 0) | (old_total > 0)), msg

    # 4. Differential against the parent commit's total.
    for name in REFERENCE_OUTPUTS:
        np.testing.assert_allclose(
            v[name].astype(float),
            v[f"reference_{name}"].astype(float),
            atol=TOL,
            err_msg=f"{name} {msg}",
        )
    np.testing.assert_allclose(old_total, reg81 + hb_reduction, atol=TOL, err_msg=msg)
    assert np.all(total <= old_total + TOL), msg
    fits = reg81 <= award
    if floor == 0:
        np.testing.assert_allclose(total[fits], old_total[fits], atol=TOL, err_msg=msg)

    # 5. Conservation: the total is what the caps take from the awards.
    removed = (award - v["uc_deductions"] - v["universal_credit"]) + (
        hb_pre - v["housing_benefit"]
    )
    np.testing.assert_allclose(total, removed, atol=TOL, err_msg=msg)

    # 6. A floor never raises the reduction reported.
    if floor:
        current_law = calculate(population, reference=False)
        assert np.all(total <= current_law["benefit_cap_reduction"] + TOL), msg


@PROPERTY_SETTINGS
@given(population=populations, floor=st.sampled_from(FLOORS))
@example(population=EXAMPLE_UNITS, floor=0.0)
@example(population=EXAMPLE_UNITS, floor=0.85)
@example(population=EXAMPLE_UNITS, floor=1.2)
@example(
    population=[
        unit(award=1.0, other_benefits=40_000.0),
        unit(award=4_999.0, other_benefits=30_000.0, childcare=2_000.0),
        unit(award=3_000.0, other_benefits=26_000.0, latent_rate=0.25, draw=0.0),
    ],
    floor=0.0,
)
@example(
    population=[
        unit(award=1.0, other_benefits=40_000.0),
        unit(award=4_999.0, other_benefits=30_000.0, childcare=2_000.0),
        unit(award=3_000.0, other_benefits=26_000.0, latent_rate=0.25, draw=0.0),
    ],
    floor=0.5,
)
def test_reduction_reported_is_what_the_cap_removes(population, floor):
    check_invariants(population, floor)


@PROPERTY_SETTINGS
@given(
    population=st.lists(
        units().filter(lambda u: u["scheme"] == "UC"), min_size=1, max_size=8
    ),
    more_benefits=st.floats(0.01, 20_000),
    more_childcare=st.floats(0.01, 10_000),
)
def test_reduction_reported_is_monotone(population, more_benefits, more_childcare):
    # 7. Current law (zero floor), with more welfare benefits or childcare.
    richer = [
        dict(u, other_benefits=u["other_benefits"] + more_benefits) for u in population
    ]
    more_care = [dict(u, childcare=u["childcare"] + more_childcare) for u in population]
    total = calculate(population + richer + more_care, reference=False)[
        "benefit_cap_reduction"
    ]
    n = len(population)
    base, up, care = total[:n], total[n : 2 * n], total[2 * n :]
    assert np.all(up >= base - TOL), population
    assert np.all(care <= base + TOL), population


def test_examples_reach_the_cases():
    """Each example exercises the case it is there for."""
    v = calculate(EXAMPLE_UNITS)
    (
        above_award,
        equal,
        childcare,
        childcare_over,
        deductions,
        whole_award,
        negative,
        hb,
        exempt,
    ) = range(9)
    # The reg. 81 amount exceeds the award: the cap removes the award, and
    # the parent commit reported the reg. 81 amount.
    assert v["uc_benefit_cap_reduction"][above_award] == 7_980
    assert v["uc_benefit_cap_reduction_after_floor"][above_award] == 100
    assert v["benefit_cap_reduction"][above_award] == 100
    assert v["reference_benefit_cap_reduction"][above_award] == 7_980
    assert v["universal_credit"][above_award] == 0
    assert v["benefit_cap_reduction"][equal] == 7_980
    assert v["universal_credit"][equal] == 0
    assert v["benefit_cap_reduction"][childcare] == 4_980
    assert v["benefit_cap_reduction"][childcare_over] == 0
    # Deductions come out of what the cap leaves, and do not change it.
    assert v["benefit_cap_reduction"][deductions] == 4_980
    assert 0 < v["uc_deductions"][deductions] < 1_020
    assert v["uc_has_deduction"][deductions]
    assert np.isclose(
        v["universal_credit"][deductions], 1_020 - v["uc_deductions"][deductions]
    )
    # The cap takes the whole award; nothing is deducted.
    assert v["uc_benefit_cap_reduction"][whole_award] > 1_000
    assert v["benefit_cap_reduction"][whole_award] == 1_000
    assert v["uc_deductions"][whole_award] == 0
    assert not v["uc_has_deduction"][whole_award]
    assert v["benefit_cap_reduction"][negative] == 0
    # Housing Benefit keeps 50 pence a week: 5,000 - 26 = 4,974.
    assert v["housing_benefit_benefit_cap_reduction"][hb] == 4_974
    assert v["benefit_cap_reduction"][hb] == 4_974
    assert v["benefit_cap_reduction"][exempt] == 0


def test_non_claimant_override_masks_applied_reduction():
    """An explicit false claim masks applied UC despite a positive award override.

    These incoherent boundary inputs are outside the generated invariants:
    the gross amount remains positive, while the applied amount and total
    are zero because uc_benefit_cap_reduction_after_floor requires a claim.
    """
    sit = situation([unit(award=100.0, other_benefits=29_900.0)])
    sit["benunits"]["b0"]["claims_universal_credit"] = {PERIOD: False}
    new = simulation(sit, floor=0.0)
    old = simulation(sit, floor=0.0, reference=True)

    assert not new.calculate("claims_universal_credit", PERIOD)[0]
    assert new.calculate("universal_credit_pre_benefit_cap", PERIOD)[0] == 100
    # relies on uc_benefit_cap_reduction being ungated; drop if it gains a claim gate.
    assert old.calculate("benefit_cap_reduction", PERIOD)[0] == 7_980
    assert new.calculate("uc_benefit_cap_reduction_after_floor", PERIOD)[0] == 0
    assert new.calculate("benefit_cap_reduction", PERIOD)[0] == 0
    assert new.calculate("universal_credit", PERIOD)[0] == 0


def test_a_binding_floor_reports_the_cap_reduction_it_leaves():
    """Under an 85% floor the deduction is met first and the cap reduction
    reported is what the floor allowance leaves of it."""
    population = [
        unit(
            award=6_000.0,
            other_benefits=21_000.0,
            latent_rate=0.25,
            combination="ADVANCE_ONLY",
            draw=0.0,
        )
    ]
    current_law = calculate(population, reference=False)
    floored = calculate(population, floor=0.85, reference=False)
    # The reg. 81 amount is the same either way: 27,000 - 22,020 = 4,980.
    assert current_law["uc_benefit_cap_reduction"][0] == 4_980
    assert floored["uc_benefit_cap_reduction"][0] == 4_980
    assert current_law["benefit_cap_reduction"][0] == 4_980
    reported = floored["benefit_cap_reduction"][0]
    # Allowance: 0.15 × £4,801.68 = £720.25. The 15% deduction (£720.25)
    # is met first, leaving nothing for the cap.
    assert np.isclose(reported, 0, atol=TOL)
    assert np.isclose(reported, floored["uc_benefit_cap_reduction_after_floor"][0])
    assert np.isclose(
        reported,
        6_000 - floored["uc_deductions"][0] - floored["universal_credit"][0],
        atol=TOL,
    )
