"""Overlapping-benefit reduction of Carer's Allowance and Carer Support Payment.

Carer's Allowance is a personal benefit that overlaps with State Pension and
with the contributory earnings-replacement benefits. The Social Security
(Overlapping Benefits) Regulations 1979 reg 12 reduce it by the other benefit,
"so however that" the allowance and the other benefit together are never less
than the unadjusted allowance. Additional pension and graduated retirement
benefit paid with an old State Pension are left out (regs 4(2)(f) and 12). The
Carer Support Payment Regulations (SSI 2023/302) reg 16(2)-(3) reduce Carer
Support Payment in the same way, to £0 where the overlapping benefit is at
least as much.

Invariants, for carers in England, Wales and Scotland in 2026, who qualify by
hours or by a reported award, with State Pension supplied directly, by
component or as a reported amount, and with other overlapping benefits:

1. Bounds: 0 <= payable <= unadjusted, for both benefits, and a person never
   has both.
2. Differential: payable equals max(0, unadjusted - overlapping), with both
   terms rebuilt here from the drawn inputs, the statutory rates and the State
   Pension type worked out below from age and gender. The reported-pension
   split follows the model's convention, as described below.
3. Monotonic: raising State Pension never raises the payable carer benefit,
   and never lowers the carer benefit and State Pension taken together.
4. Entitlement survives: raising State Pension leaves the carer's entitlement,
   carer status and Pension Credit carer addition unchanged (SPC Regs Sch I
   para 4(2) turns on entitlement, not payment).
5. The Scottish Carer Supplement is paid exactly when Carer Support Payment is
   payable (CSP Regs reg 14A), at its full rate.
6. Claiming a benefit the overlap reduces to nil creates entitlement: where a
   pension-age carer's State Pension is at least the carer benefit, the carer
   benefit, Pension Credit income and income tax are the same whether or not
   they would claim. Claiming unlocks the Pension Credit carer addition
   (SPC Regs Sch I para 4(2)). Below the minimum guarantee, Guarantee Credit
   and Pension Credit increase by exactly that addition.
7. Pension Credit counts the payable amount (SPC Regs reg 15(3)-(4)(a), (g)):
   for a pensioner below the personal allowance, Pension Credit income is
   State Pension plus private pension plus the payable carer benefit.

The reference uses the statutory pension cutoff and these model conventions:
- Whole ages with the default six months since the last birthday infer
  6 April birthdays. At 6 October 2026, pensionable age has been attained
  from age 66; the old State Pension starts at 76 for men and 74 for women.
  Pensions Act 2014 s. 1(2) requires attainment before 6 April 2016: a man
  aged 75 was born on 6 April 1951 and attains pensionable age on that
  cutoff day, so has a new State Pension. The reference computes the type
  independently of the model's calculated state_pension_type.
- A State Pension supplied directly, with no components, overlaps in full.
- A reported old State Pension is split at the full basic rate, and the
  excess is treated as additional pension, which does not overlap. Basic
  pension increments above that rate, or additional pension within a partial
  pension below it, would be split differently in law.
- The reduction compares annual amounts. With the same underlying year-round
  carer entitlement, annual netting is a lower bound on the weekly payable
  total. These assertions check annual netting and do not infer the dates or
  duration of overlapping awards.
"""

import numpy as np
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
WEEKS = 52
TOLERANCE = 0.01
PROPERTY_SETTINGS = settings(
    max_examples=12,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
COUNTRIES = ["ENGLAND", "WALES", "SCOTLAND"]
STATE_PENSION_MODES = ["none", "direct", "components", "reported"]
OTHER_OVERLAPPING = [
    "esa_contrib_reported",
    "jsa_contrib_reported",
    "incapacity_benefit_reported",
    "maternity_allowance_reported",
]
# Whole ages with the six-month default imply 6 April birthdays. These are
# the attainment and old-pension thresholds at 6 October 2026, independently
# of the model's calculated type. Pensions Act 2014 s.1(2) says "before
# 6 April 2016": men aged 75 attain on that date, whereas those aged 76
# attained on 6 April 2015. Women born on 6 April 1952 attained on 6 May 2014;
# those born on 6 April 1953 attained on 6 July 2016 (1995 Act Sch 4 table 1).
STATE_PENSION_AGE = 66
OLD_STATE_PENSION_AGE = {"MALE": 76, "FEMALE": 74}


class CarerOverlapSimulation(Simulation):
    """Label the synthetic dataset with the same year as its pension inputs."""

    default_input_period = YEAR
    default_calculation_period = YEAR


def pension_type_for(person):
    age = person["age"]
    if age < STATE_PENSION_AGE:
        return "NONE"
    if age >= OLD_STATE_PENSION_AGE[person.get("gender", "MALE")]:
        return "BASIC"
    return "NEW"


def money(high):
    return st.floats(0, high, allow_nan=False, allow_infinity=False).map(
        lambda x: round(x, 2)
    )


@st.composite
def carers(draw, min_size=1, max_size=6):
    """A list of single-adult households, each with one potential carer."""
    n = draw(st.integers(min_size, max_size))
    mode = draw(st.sampled_from(STATE_PENSION_MODES))
    people = []
    for _ in range(n):
        person = {
            "age": draw(st.integers(25, 95)),
            "gender": draw(st.sampled_from(["MALE", "FEMALE"])),
            "country": draw(st.sampled_from(COUNTRIES)),
            "care_hours": draw(st.sampled_from([0, 20, 35, 60])),
            "carers_allowance_reported": draw(st.sampled_from([0, 1, 4_000])),
            "would_claim_carers_allowance": draw(st.booleans()),
            "mode": mode,
            # Amounts straddle the carer benefit (about £4,495 a year) and the
            # full basic and new State Pension rates; half the draws fall
            # below the carer benefit, where the overlap leaves some payable.
            "pension": draw(st.one_of(money(4_400), money(16_000))),
            "additional": draw(money(6_000)),
            "extra": draw(money(8_000)),
            # Other overlapping benefits are rare, so they do not mask the
            # State Pension overlap in most draws.
            "other": {
                variable: draw(st.sampled_from([0] * 9 + [1_500, 4_495.4, 9_000]))
                for variable in OTHER_OVERLAPPING
            },
        }
        people.append(person)
    return people


def state_pension_inputs(person, extra=0.0):
    """Inputs for the person's State Pension, with ``extra`` added to it."""
    mode, pension = person["mode"], person["pension"] + extra
    pension_type = pension_type_for(person)
    if mode == "direct":
        return {"state_pension": pension}
    if mode == "reported":
        return {"state_pension_reported": pension}
    if mode == "components":
        # The flat-rate component follows the type. With an old State
        # Pension the additional amount is additional pension; with a new
        # one it is a protected payment. No one gets either before reaching
        # pensionable age.
        return {
            "basic_state_pension": pension if pension_type == "BASIC" else 0,
            "new_state_pension": pension if pension_type == "NEW" else 0,
            "additional_state_pension": (
                person["additional"] if pension_type != "NONE" else 0
            ),
        }
    return {}


def build(people, extra=None, **overrides):
    """One simulation holding every drawn person in their own household.

    A supplied input overrides its variable's formula for the whole
    population; unspecified people receive that variable's default value.
    Use one State Pension input mode per batch so a direct pension or an
    explicit component cannot replace another person's calculated pension.
    """
    assert len({person["mode"] for person in people}) == 1
    extra = extra or [0.0] * len(people)
    situation = {"people": {}, "benunits": {}, "households": {}}
    for i, person in enumerate(people):
        inputs = {
            "age": person["age"],
            "gender": person.get("gender", "MALE"),
            "care_hours": person["care_hours"],
            "carers_allowance_reported": person["carers_allowance_reported"],
            "would_claim_carers_allowance": person["would_claim_carers_allowance"],
            **person["other"],
            **state_pension_inputs(person, extra[i]),
            **person.get("person_inputs", {}),
        }
        inputs.update(overrides)
        household = {"country": person["country"], **person.get("household_inputs", {})}
        situation["people"][f"p{i}"] = {k: {YEAR: v} for k, v in inputs.items()}
        situation["benunits"][f"b{i}"] = {"members": [f"p{i}"]}
        situation["households"][f"h{i}"] = {
            "members": [f"p{i}"],
            **{k: {YEAR: v} for k, v in household.items()},
        }
    return CarerOverlapSimulation(situation=situation)


def calc(sim, variable):
    return np.asarray(sim.calculate(variable, YEAR), dtype=float)


def rates(sim):
    parameters = sim.tax_benefit_system.parameters(f"{YEAR}-06-01")
    return {
        "ca": float(parameters.gov.dwp.carers_allowance.rate) * WEEKS,
        "csp": float(parameters.gov.social_security_scotland.carer_support_payment.rate)
        * WEEKS,
        "supplement": float(
            parameters.gov.social_security_scotland.carer_support_payment.supplement
        )
        * WEEKS,
        "basic": float(parameters.gov.dwp.state_pension.basic_state_pension.amount)
        * WEEKS,
        "min_hours": float(parameters.gov.dwp.carers_allowance.min_hours),
        "carer_addition": float(
            parameters.gov.dwp.pension_credit.guarantee_credit.carer.addition
        )
        * WEEKS,
    }


def reference(people, sim, extra=None):
    """Unadjusted and overlapping amounts rebuilt from the drawn inputs."""
    extra = extra or [0.0] * len(people)
    r = rates(sim)
    unadjusted_ca, unadjusted_csp, overlapping = [], [], []
    for i, person in enumerate(people):
        qualifies = (
            person["care_hours"] >= r["min_hours"]
            or person["carers_allowance_reported"] > 0
        ) and person["would_claim_carers_allowance"]
        scottish = person["country"] == "SCOTLAND"
        unadjusted_ca.append(r["ca"] * (qualifies and not scottish))
        unadjusted_csp.append(r["csp"] * (qualifies and scottish))
        pension_type = pension_type_for(person)
        pension = person["pension"] + extra[i]
        mode = person["mode"]
        if mode == "direct":
            # The model's convention: with no components, all of it overlaps.
            state_pension = pension
        elif mode == "reported":
            # The model's split of a reported amount: an old State Pension
            # above the full basic rate is additional pension, which does not
            # overlap. A new State Pension overlaps in full, protected payment
            # included, and there is none before pensionable age.
            state_pension = {
                "BASIC": min(pension, r["basic"]),
                "NEW": pension,
                "NONE": 0,
            }[pension_type]
        elif mode == "components":
            state_pension = {
                "BASIC": pension,
                "NEW": pension + person["additional"],
                "NONE": 0,
            }[pension_type]
        else:
            state_pension = 0
        # sda is not drawn, so the other overlapping benefits are the four
        # reported contributory benefits.
        overlapping.append(state_pension + sum(person["other"].values()))
    return (
        np.array(unadjusted_ca),
        np.array(unadjusted_csp),
        np.array(overlapping),
    )


def pinned(age, country, mode, pension, additional=0.0, gender="MALE"):
    """A qualifying carer with no other overlapping benefit."""
    return {
        "age": age,
        "gender": gender,
        "country": country,
        "care_hours": 35,
        "carers_allowance_reported": 0,
        "would_claim_carers_allowance": True,
        "mode": mode,
        "pension": pension,
        "additional": additional,
        "extra": 0.0,
        "other": {variable: 0 for variable in OTHER_OVERLAPPING},
    }


@PROPERTY_SETTINGS
@given(people=carers())
# An old State Pension below the carer benefit, with additional pension that
# must not overlap, and a new State Pension whose protected payment must.
@example(
    people=[
        pinned(80, "ENGLAND", "components", 2_000, 5_000),
        pinned(80, "SCOTLAND", "components", 2_000, 5_000, "FEMALE"),
        pinned(68, "ENGLAND", "components", 2_000, 1_000, "FEMALE"),
        pinned(68, "SCOTLAND", "components", 2_000, 1_000),
        # The same inferred birthday belongs to different systems for men
        # and women under the statutory timetable.
        pinned(74, "ENGLAND", "components", 2_000, 5_000),
        pinned(74, "SCOTLAND", "components", 2_000, 5_000, "FEMALE"),
        # Attainment on 6 April 2016 means new pension; before it means old.
        pinned(75, "ENGLAND", "components", 2_000, 5_000),
        pinned(76, "ENGLAND", "components", 2_000, 5_000),
        pinned(66, "WALES", "components", 2_000, 1_000),
    ]
)
@example(people=[pinned(80, "WALES", "reported", 3_000)])
@example(people=[pinned(70, "ENGLAND", "direct", 4_495.4)])
def test_overlap_bounds_and_reference(people):
    sim = build(people)
    ca, csp = calc(sim, "carers_allowance"), calc(sim, "carer_support_payment")
    ca_pre = calc(sim, "carers_allowance_pre_overlap")
    csp_pre = calc(sim, "carer_support_payment_pre_overlap")
    ref_ca_pre, ref_csp_pre, ref_overlap = reference(people, sim)

    # Components are assigned using age and gender, independently of the
    # model's calculated type. Check the default-birthday reference as well.
    pension_type = sim.calculate("state_pension_type", YEAR)
    if hasattr(pension_type, "decode_to_str"):
        pension_type = pension_type.decode_to_str()
    pension_type = np.asarray(pension_type).astype(str)
    assert list(pension_type) == [pension_type_for(p) for p in people]

    # 1. Bounds, and no one has both benefits.
    assert (ca >= 0).all() and (csp >= 0).all()
    assert (ca <= ca_pre + TOLERANCE).all()
    assert (csp <= csp_pre + TOLERANCE).all()
    assert not ((ca > 0) & (csp > 0)).any()
    assert not ((ca_pre > 0) & (csp_pre > 0)).any()

    ca_overlap = calc(sim, "carers_allowance_overlapping_benefits")
    csp_overlap = calc(sim, "carer_support_payment_overlapping_benefits")

    # 2. Differential against amounts rebuilt from the inputs.
    np.testing.assert_allclose(ca_pre, ref_ca_pre, atol=TOLERANCE)
    np.testing.assert_allclose(csp_pre, ref_csp_pre, atol=TOLERANCE)
    np.testing.assert_allclose(ca_overlap, ref_overlap, atol=TOLERANCE)
    np.testing.assert_allclose(csp_overlap, ref_overlap, atol=TOLERANCE)
    np.testing.assert_allclose(
        ca, np.maximum(ref_ca_pre - ref_overlap, 0), atol=TOLERANCE
    )
    np.testing.assert_allclose(
        csp, np.maximum(ref_csp_pre - ref_overlap, 0), atol=TOLERANCE
    )

    # 5. Scottish Carer Supplement only, and in full, with a payable CSP.
    supplement = calc(sim, "scottish_carer_supplement")
    np.testing.assert_allclose(
        supplement, (csp > 0) * rates(sim)["supplement"], atol=TOLERANCE
    )


@PROPERTY_SETTINGS
@given(people=carers())
def test_carer_benefit_is_monotonic_in_state_pension(people):
    drawn = [p for p in people if p["mode"] != "none"]
    if not drawn:
        return
    extra = [p["extra"] for p in drawn]
    low, high = build(drawn), build(drawn, extra=extra)

    for benefit in ["carers_allowance", "carer_support_payment"]:
        before, after = calc(low, benefit), calc(high, benefit)
        # 3. More State Pension never raises the carer benefit...
        assert (after <= before + TOLERANCE).all()
        # ...and never lowers the two together.
        together_before = before + calc(low, "state_pension")
        together_after = after + calc(high, "state_pension")
        assert (together_after >= together_before - TOLERANCE).all()

    # 4. Entitlement and carer status do not depend on State Pension.
    for variable in [
        "carers_allowance_pre_overlap",
        "carer_support_payment_pre_overlap",
        "is_entitled_to_carer_benefit",
        "is_carer_for_benefits",
        "carer_minimum_guarantee_addition",
    ]:
        np.testing.assert_allclose(calc(low, variable), calc(high, variable))


@st.composite
def overlapped_pensioners(draw):
    """Fully overlapped carers with income below the minimum guarantee."""
    n = draw(st.integers(1, 4))
    return [
        {
            "age": draw(st.integers(67, 90)),
            "country": draw(st.sampled_from(COUNTRIES)),
            "care_hours": draw(st.sampled_from([35, 60])),
            "carers_allowance_reported": 0,
            "would_claim_carers_allowance": True,
            "mode": "direct",
            # At least the 2026-27 carer benefit of £86.45 a week.
            "pension": draw(
                st.floats(4_495.4, 10_000, allow_nan=False).map(lambda x: round(x, 2))
            ),
            "additional": 0,
            "extra": 0,
            "other": {variable: 0 for variable in OTHER_OVERLAPPING},
            "person_inputs": {"private_pension_income": draw(money(1_000))},
            "household_inputs": {
                "rent": draw(st.sampled_from([0, 5_000])),
                "tenure_type": "RENT_FROM_COUNCIL",
            },
        }
        for _ in range(n)
    ]


@settings(
    max_examples=8,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(people=overlapped_pensioners())
def test_claiming_a_carer_benefit_reduced_to_nil_increases_pension_credit(people):
    claims = build(people, would_claim_carers_allowance=True)
    does_not = build(people, would_claim_carers_allowance=False)
    # 6. The benefit is not payable either way; claiming establishes the
    # entitlement needed for the carer addition.
    for sim in [claims, does_not]:
        assert (calc(sim, "carers_allowance") == 0).all()
        assert (calc(sim, "carer_support_payment") == 0).all()
        assert (calc(sim, "scottish_carer_supplement") == 0).all()
    assert (calc(claims, "is_entitled_to_carer_benefit") == 1).all()
    assert (calc(does_not, "is_entitled_to_carer_benefit") == 0).all()
    for variable in ["pension_credit_income", "income_tax"]:
        np.testing.assert_allclose(
            calc(claims, variable), calc(does_not, variable), atol=TOLERANCE
        )
    addition = rates(claims)["carer_addition"]
    np.testing.assert_allclose(
        calc(claims, "carer_minimum_guarantee_addition"), addition, atol=TOLERANCE
    )
    assert (calc(does_not, "carer_minimum_guarantee_addition") == 0).all()
    np.testing.assert_allclose(
        calc(claims, "minimum_guarantee") - calc(does_not, "minimum_guarantee"),
        addition,
        atol=TOLERANCE,
    )
    assert (calc(does_not, "guarantee_credit") > 0).all()
    for variable in ["guarantee_credit", "pension_credit"]:
        np.testing.assert_allclose(
            calc(claims, variable) - calc(does_not, variable), addition, atol=TOLERANCE
        )


@st.composite
def low_income_pensioners(draw):
    """Pension-age carers whose income stays below the personal allowance."""
    n = draw(st.integers(1, 6))
    return [
        {
            "age": draw(st.integers(67, 90)),
            "country": draw(st.sampled_from(COUNTRIES)),
            "care_hours": 35,
            "carers_allowance_reported": 0,
            "would_claim_carers_allowance": True,
            "mode": "direct",
            "pension": draw(money(7_000)),
            "additional": 0,
            "extra": 0,
            "other": {variable: 0 for variable in OTHER_OVERLAPPING},
            "person_inputs": {"private_pension_income": draw(money(1_000))},
        }
        for _ in range(n)
    ]


@PROPERTY_SETTINGS
@given(people=low_income_pensioners())
def test_pension_credit_counts_the_payable_carer_benefit(people):
    sim = build(people)
    private = np.array([p["person_inputs"]["private_pension_income"] for p in people])
    state_pension = np.array([p["pension"] for p in people])
    payable = calc(sim, "carers_allowance") + calc(sim, "carer_support_payment")
    unadjusted = rates(sim)["ca"]

    # 7. Income is at most £7,000 + £1,000 + £4,495.40, below the £12,570
    # personal allowance, so Pension Credit income has no tax deducted.
    assert (calc(sim, "income_tax") == 0).all()
    np.testing.assert_allclose(
        calc(sim, "pension_credit_income"),
        state_pension + private + payable,
        atol=TOLERANCE,
    )
    # The carer's State Pension and carer benefit together are the larger of
    # the two, never their sum.
    np.testing.assert_allclose(
        state_pension + payable,
        np.maximum(state_pension, unadjusted),
        atol=TOLERANCE,
    )
