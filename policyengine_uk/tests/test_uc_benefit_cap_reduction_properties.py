"""Property and differential tests for the amount the benefit cap removes
from a Universal Credit award.

``uc_benefit_cap_reduction_before_award_limit`` is the UC Regs 2013 reg. 81
amount: the excess of the welfare benefits over the Universal Credit cap,
less the childcare costs element, on an award only. It can exceed the award
before the cap. ``uc_benefit_cap_reduction`` is the part the award can bear,
``min(reg. 81 amount, award before the cap)``: what the cap takes from the
award. ``benefit_cap_reduction`` adds it to the Housing Benefit reduction (HB
Regs 2006 reg. 75D), and policyengine-uk-data calibrates that total against
DWP's benefit cap statistics.

``REFERENCE_WIRING`` restores the parent commit (c8fd1c9d1), where
``uc_benefit_cap_reduction`` was the reg. 81 amount and ``universal_credit``,
``uc_deductions`` and ``uc_has_deduction`` read it.

Invariants, over generated benefit units and the explicit examples, under
current law and under protected floors of 0.5, 0.85, 1 and 1.2:

1. Definition. The reg. 81 amount is ``max(max(W - cap, 0) - childcare, 0)``
   where the award before the cap is positive, and 0 otherwise.
2. Bound. ``uc_benefit_cap_reduction = min(reg. 81 amount, max(award before
   the cap, 0))``, so it is between 0 and each of the two.
3. Incidence. ``uc_benefit_cap_reduction > 0`` exactly where the reg. 81
   amount is positive, so uk-data's count of capped households is unchanged.
4. Differential. ``universal_credit``, ``uc_deductions`` and
   ``uc_has_deduction`` equal the parent commit's, for every floor.
5. Conservation under current law. ``universal_credit = max(award before the
   cap, 0) - uc_benefit_cap_reduction - uc_deductions`` and ``housing_benefit
   = Housing Benefit before the cap - its reduction``, so
   ``benefit_cap_reduction`` is exactly what the two caps take from the
   awards.
6. Under a protected floor, ``universal_credit`` lies between that
   current-law amount and the award before the cap.
7. Monotonicity. With the award before the cap fixed,
   ``uc_benefit_cap_reduction`` does not fall as the welfare benefits rise,
   and does not rise as the childcare costs element rises.
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
PROPERTY_SETTINGS = settings(
    max_examples=25,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


# ---------------------------------------------------------------------------
# The parent commit's wiring: the reduction the award reads is the reg. 81
# amount itself (verbatim formula).


def _reference_uc_benefit_cap_reduction():
    class uc_benefit_cap_reduction(Variable):
        value_type = float
        entity = BenUnit
        label = "Universal Credit benefit cap reduction (parent commit)"
        definition_period = YEAR
        unit = GBP

        def formula(benunit, period, parameters):
            excess = max_(
                benunit("benefit_cap_welfare_benefits", period)
                - benunit("uc_benefit_cap", period),
                0,
            )
            reduction = max_(excess - benunit("uc_childcare_element", period), 0)
            has_award = benunit("universal_credit_pre_benefit_cap", period) > 0
            return where(has_award, reduction, 0)

    return uc_benefit_cap_reduction


class REFERENCE_WIRING(Reform):
    def apply(self):
        self.update_variable(_reference_uc_benefit_cap_reduction())


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
        # The task's case: UC before the cap 100, welfare benefits 30,000,
        # cap 22,020. Reg. 81 says 7,980; the award can bear 100.
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
    "uc_benefit_cap_reduction_before_award_limit",
    "uc_benefit_cap_reduction",
    "uc_deductions",
    "uc_has_deduction",
    "uc_standard_allowance",
    "universal_credit",
    "housing_benefit_pre_benefit_cap",
    "housing_benefit_benefit_cap_reduction",
    "housing_benefit",
    "benefit_cap_reduction",
]
REFERENCE_OUTPUTS = ["universal_credit", "uc_deductions", "uc_has_deduction"]


def floor_reform(floor):
    return {
        "gov.dwp.universal_credit.deductions.protected_floor": {
            f"{PERIOD}-01-01.{PERIOD}-12-31": floor
        }
    }


def calculate(population, floor=0.0):
    sit = situation(population)
    new = Simulation(situation=sit, reform=floor_reform(floor))
    old = Simulation(situation=sit, reform=(REFERENCE_WIRING, floor_reform(floor)))
    v = {name: np.asarray(new.calculate(name, PERIOD)) for name in VARIABLES}
    for name in REFERENCE_OUTPUTS:
        v[f"reference_{name}"] = np.asarray(old.calculate(name, PERIOD))
    v["reference_uc_benefit_cap_reduction"] = np.asarray(
        old.calculate("uc_benefit_cap_reduction", PERIOD)
    )
    return v


# ---------------------------------------------------------------------------
# Properties.


def check_invariants(population, floor):
    v = calculate(population, floor)
    msg = f"floor={floor} {population}"
    pre = v["universal_credit_pre_benefit_cap"]
    award = np.maximum(pre, 0)
    reg81 = v["uc_benefit_cap_reduction_before_award_limit"]
    reduction = v["uc_benefit_cap_reduction"]

    # 1. Definition (reg. 81, on an award only).
    excess = np.maximum(v["benefit_cap_welfare_benefits"] - v["uc_benefit_cap"], 0)
    np.testing.assert_allclose(
        reg81,
        np.where(pre > 0, np.maximum(excess - v["uc_childcare_element"], 0), 0),
        atol=TOL,
        err_msg=msg,
    )
    # The parent commit's reduction is the reg. 81 amount.
    np.testing.assert_allclose(
        v["reference_uc_benefit_cap_reduction"], reg81, atol=TOL, err_msg=msg
    )

    # 2. Bound.
    np.testing.assert_allclose(
        reduction, np.minimum(reg81, award), atol=TOL, err_msg=msg
    )
    assert np.all(reduction >= 0), msg
    assert np.all(reduction <= reg81 + TOL), msg
    assert np.all(reduction <= award + TOL), msg

    # 3. Incidence.
    np.testing.assert_array_equal(reduction > 0, reg81 > 0, err_msg=msg)

    # 4. Differential against the parent commit's wiring.
    for name in REFERENCE_OUTPUTS:
        np.testing.assert_allclose(
            v[name].astype(float),
            v[f"reference_{name}"].astype(float),
            atol=TOL,
            err_msg=f"{name} {msg}",
        )

    # 5 and 6. Conservation, and the protected floor.
    current_law = award - reduction - v["uc_deductions"]
    assert np.all(current_law >= -TOL), msg
    if floor == 0:
        np.testing.assert_allclose(
            v["universal_credit"], current_law, atol=TOL, err_msg=msg
        )
    else:
        assert np.all(v["universal_credit"] >= current_law - TOL), msg
        assert np.all(v["universal_credit"] <= award + TOL), msg
    hb_pre = v["housing_benefit_pre_benefit_cap"]
    hb_reduction = v["housing_benefit_benefit_cap_reduction"]
    np.testing.assert_allclose(
        v["housing_benefit"], hb_pre - hb_reduction, atol=TOL, err_msg=msg
    )
    np.testing.assert_allclose(
        v["benefit_cap_reduction"], reduction + hb_reduction, atol=TOL, err_msg=msg
    )
    if floor == 0:
        removed = (award - v["uc_deductions"] - v["universal_credit"]) + (
            hb_pre - v["housing_benefit"]
        )
        np.testing.assert_allclose(
            v["benefit_cap_reduction"], removed, atol=TOL, err_msg=msg
        )


@PROPERTY_SETTINGS
@given(population=populations, floor=st.sampled_from(FLOORS))
@example(population=EXAMPLE_UNITS, floor=0.0)
@example(population=EXAMPLE_UNITS, floor=0.85)
@example(population=EXAMPLE_UNITS, floor=1.2)
def test_reduction_is_what_the_cap_removes(population, floor):
    check_invariants(population, floor)


@PROPERTY_SETTINGS
@given(
    population=st.lists(
        units().filter(lambda u: u["scheme"] == "UC"), min_size=1, max_size=8
    ),
    more_benefits=st.floats(0.01, 20_000),
    more_childcare=st.floats(0.01, 10_000),
)
def test_reduction_is_monotone(population, more_benefits, more_childcare):
    # 7. Each unit, with more welfare benefits, and with more childcare.
    richer = [
        dict(u, other_benefits=u["other_benefits"] + more_benefits) for u in population
    ]
    more_care = [
        dict(u, childcare=u["childcare"] + more_childcare) for u in population
    ]
    v = calculate(population + richer + more_care)
    n = len(population)
    base, up, care = (
        v["uc_benefit_cap_reduction"][:n],
        v["uc_benefit_cap_reduction"][n : 2 * n],
        v["uc_benefit_cap_reduction"][2 * n :],
    )
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
    # The reg. 81 amount exceeds the award: the cap removes the award.
    assert v["uc_benefit_cap_reduction_before_award_limit"][above_award] == 7_980
    assert v["uc_benefit_cap_reduction"][above_award] == 100
    assert v["benefit_cap_reduction"][above_award] == 100
    assert v["universal_credit"][above_award] == 0
    assert v["uc_benefit_cap_reduction"][equal] == 7_980
    assert v["universal_credit"][equal] == 0
    assert v["uc_benefit_cap_reduction"][childcare] == 4_980
    assert v["uc_benefit_cap_reduction"][childcare_over] == 0
    # Deductions come out of what the cap leaves.
    assert v["uc_benefit_cap_reduction"][deductions] == 4_980
    assert 0 < v["uc_deductions"][deductions] < 1_020
    assert v["uc_has_deduction"][deductions]
    assert np.isclose(
        v["universal_credit"][deductions], 1_020 - v["uc_deductions"][deductions]
    )
    # The cap takes the whole award; nothing is deducted.
    assert v["uc_benefit_cap_reduction_before_award_limit"][whole_award] > 1_000
    assert v["uc_benefit_cap_reduction"][whole_award] == 1_000
    assert v["uc_deductions"][whole_award] == 0
    assert not v["uc_has_deduction"][whole_award]
    assert v["uc_benefit_cap_reduction"][negative] == 0
    # Housing Benefit keeps 50 pence a week: 5,000 - 26 = 4,974.
    assert v["housing_benefit_benefit_cap_reduction"][hb] == 4_974
    assert v["benefit_cap_reduction"][hb] == 4_974
    assert v["benefit_cap_reduction"][exempt] == 0
