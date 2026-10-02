"""Property-based tests for Pension Credit recipients under the national
pensioner council tax reduction schemes (England pensioners, Wales, Scotland).

Law:
- Guarantee credit: "the whole of his capital and income must be disregarded"
  (SI 2012/2885 Sch 1 para 13; WSI 2013/3029 Sch 1 para 7; SSI 2012/319 reg
  24). Capital for the 16,000 limit is calculated under the same Part (SI
  2012/2885 reg 11(3); WSI 2013/3029 reg 30(2)), so the limit cannot apply.
  The award is the maximum reduction less non-dependant deductions.
- Savings credit only: the Secretary of State's assessment of income and
  capital is used, adjusted for the savings credit payable (SI 2012/2885 Sch 1
  para 14; WSI 2013/3029 Sch 1 para 8; SSI 2012/319 reg 25).

Invariants, for any generated population of families, where L is the eligible
liability, ND the non-dependant deductions and A the applicable amount:

1. Structural: 0 <= CTR <= L; receipt of guarantee credit and receipt of
   savings credit only are mutually exclusive, and each requires Pension Credit
   eligibility and take-up.
2. Guarantee credit recipients get exactly max(0, L - ND).
3. Savings-credit-only recipients get max(0, L - 0.2 x max(0, PC income + SC -
   A) - ND) when the Pension Credit assessment of capital is within 16,000, and
   nothing otherwise.
4. Differential: everyone else keeps the previous formula, max(0, L - 0.2 x
   max(0, I - A) - ND) when household savings are within 16,000, where I is the
   income definition on main before this change, recomputed here from its
   components rather than read from the variable under test.
5. Metamorphic: a guarantee credit recipient's CTR does not change when the
   State Pension changes.
6. Metamorphic: nor when its savings change.
7. Metamorphic: not claiming Pension Credit never raises a guarantee credit
   recipient's CTR, and a non-claimant is assessed under invariant 4.
8. Under the Pension Credit freeze, receipt and the savings credit payable
   follow the frozen (baseline) award, even where the reform alone would
   change which credit is received.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Local authorities without a modelled local scheme, so each country's
# national scheme (England: pensioners only) applies.
COUNTRIES = {
    "ENGLAND": "MAIDSTONE",
    "WALES": "CARDIFF",
    "SCOTLAND": "GLASGOW_CITY",
}
# 67 and over is unambiguously over State Pension age in 2026-27. Savings
# credit needs State Pension age reached before April 2016, so half the draws
# are 80 or over.
PENSION_AGE = st.one_of(st.integers(67, 79), st.integers(80, 100))
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single_pension": [PENSION_AGE],
    "couple_pension": [PENSION_AGE, PENSION_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
    "single_working": [WORKING_AGE],
}
# Half the State Pension draws fall around the minimum guarantee, where
# guarantee credit, savings credit and the CTR taper all meet.
state_pension = st.one_of(
    st.floats(0, 25_000, allow_nan=False, allow_infinity=False),
    st.floats(10_000, 16_000, allow_nan=False, allow_infinity=False),
)
# Half the populations get a standard minimum guarantee above the CTR
# applicable amount (256.00 single, 383.35 couple a week), as an
# earnings-linked guarantee path produces, so guarantee credit recipients can
# have income above the applicable amount. Applied as a reform to the whole
# population: a minimum_guarantee input on some benefit units would set it to
# zero on every other one.
guarantees = st.one_of(st.none(), st.floats(240, 450))
CAPITAL_LIMIT = 16_000
WITHDRAWAL_RATE = 0.2


@st.composite
def families(draw):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    pension_shape = shape != "single_working"
    return dict(
        shape=shape,
        ages=[draw(age) for age in SHAPES[shape]],
        country=draw(st.sampled_from(sorted(COUNTRIES))),
        council_tax=draw(st.floats(500, 4_000)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
        other_property=draw(st.one_of(st.just(0.0), st.floats(0, 10_000))),
        state_pension=draw(state_pension),
        private_pension=draw(st.one_of(st.just(0.0), st.floats(0, 5_000))),
        employment_income=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
        # Other income main's CTR definition counts, so the differential
        # (invariant 4) sees more than pensions and earnings.
        self_employment_income=draw(st.one_of(st.just(0.0), st.floats(0, 15_000))),
        property_income=draw(st.one_of(st.just(0.0), st.floats(0, 5_000))),
        carers_allowance=draw(st.one_of(st.just(0.0), st.floats(0, 4_500))),
        child_ages=draw(st.lists(st.integers(1, 15), max_size=2)),
        would_claim_uc=draw(st.booleans()),
        would_claim_pc=draw(st.sampled_from([True, True, False])),
        # A working-age non-dependant (a separate benefit unit) living with a
        # pension-age family; younger than the claimant, so never the head.
        non_dependant_income=(
            draw(st.one_of(st.none(), st.floats(0, 15_000))) if pension_shape else None
        ),
    )


@st.composite
def savings_credit_families(draw):
    """Single pensioners who reached State Pension age before April 2016 with
    income just above the minimum guarantee, the savings credit range."""
    return dict(
        shape="single_pension",
        ages=[draw(st.integers(80, 100))],
        country=draw(st.sampled_from(sorted(COUNTRIES))),
        council_tax=draw(st.floats(500, 4_000)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 25_000))),
        other_property=draw(st.one_of(st.just(0.0), st.floats(0, 10_000))),
        state_pension=draw(st.floats(12_400, 15_000)),
        private_pension=draw(st.one_of(st.just(0.0), st.floats(0, 1_500))),
        employment_income=0.0,
        would_claim_pc=True,
        non_dependant_income=draw(st.one_of(st.none(), st.floats(0, 15_000))),
    )


@st.composite
def guarantee_credit_families(draw):
    """Pensioners claiming Pension Credit with income low enough to keep a
    guarantee credit under the State Pension and savings changes the
    metamorphic tests make."""
    shape = draw(st.sampled_from(["single_pension", "couple_pension"]))
    return dict(
        shape=shape,
        ages=[draw(PENSION_AGE) for _ in SHAPES[shape]],
        country=draw(st.sampled_from(sorted(COUNTRIES))),
        council_tax=draw(st.floats(500, 4_000)),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
        other_property=0.0,
        state_pension=draw(st.floats(0, 5_000)),
        private_pension=0.0,
        employment_income=0.0,
        would_claim_pc=True,
        non_dependant_income=draw(st.one_of(st.none(), st.floats(0, 15_000))),
    )


# Random families, plus a few that are sure to receive guarantee credit, so
# the metamorphic tests always have recipients to check.
populations = st.builds(
    lambda random, recipients: random + recipients,
    st.lists(families(), min_size=15, max_size=30),
    st.lists(guarantee_credit_families(), min_size=3, max_size=6),
)


def situation(
    units,
    state_pension_change=0.0,
    savings_change=0.0,
    would_claim_pc=None,
):
    people, benunits, households = {}, {}, {}
    claimant_benunits = []
    benunit_index = 0
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            person = {"age": {YEAR: age}}
            if age >= 67:
                person["state_pension"] = {
                    YEAR: max(0.0, unit["state_pension"] + state_pension_change)
                }
                person["private_pension_income"] = {YEAR: unit["private_pension"]}
            else:
                person["employment_income"] = {YEAR: unit["employment_income"]}
                person["self_employment_income"] = {
                    YEAR: unit.get("self_employment_income", 0.0)
                }
            if j == 0:
                person["property_income"] = {YEAR: unit.get("property_income", 0.0)}
                person["carers_allowance"] = {YEAR: unit.get("carers_allowance", 0.0)}
            people[name] = person
            names.append(name)
        for k, child_age in enumerate(unit.get("child_ages", [])):
            name = f"c{i}_{k}"
            people[name] = {"age": {YEAR: child_age}}
            names.append(name)
        claim_pc = unit["would_claim_pc"] if would_claim_pc is None else would_claim_pc
        benunit = {
            "members": names,
            # claims_all_entitled_benefits sums reported benefits across the
            # whole simulation, so set it for every family.
            "claims_all_entitled_benefits": {YEAR: True},
            "would_claim_pc": {YEAR: claim_pc},
            "would_claim_uc": {YEAR: unit.get("would_claim_uc", False)},
        }
        benunits[f"b{i}"] = benunit
        claimant_benunits.append(benunit_index)
        benunit_index += 1
        household_members = list(names)
        if unit["non_dependant_income"] is not None:
            name = f"n{i}"
            people[name] = {
                "age": {YEAR: 40},
                "employment_income": {YEAR: unit["non_dependant_income"]},
            }
            benunits[f"n{i}"] = {
                "members": [name],
                "claims_all_entitled_benefits": {YEAR: True},
                "would_claim_uc": {YEAR: False},
            }
            benunit_index += 1
            household_members.append(name)
        households[f"h{i}"] = {
            "members": household_members,
            "country": {YEAR: unit["country"]},
            "local_authority": {YEAR: COUNTRIES[unit["country"]]},
            "tenure_type": {YEAR: "OWNED_OUTRIGHT"},
            "council_tax": {YEAR: unit["council_tax"]},
            "savings": {YEAR: max(0.0, unit["savings"] + savings_change)},
            "other_residential_property_value": {YEAR: unit["other_property"]},
        }
    return (
        {"people": people, "benunits": benunits, "households": households},
        np.array(claimant_benunits),
    )


BENUNIT_VARIABLES = [
    "simulated_council_tax_reduction_benunit",
    "council_tax_reduction_applicable_amount",
    "council_tax_reduction_applicable_income",
    "council_tax_reduction_non_dep_deductions",
    "in_receipt_of_guarantee_credit",
    "in_receipt_of_savings_credit_only",
    "is_pension_credit_eligible",
    "would_claim_pc",
    "guarantee_credit",
    "savings_credit",
    "pension_credit_income",
    "pension_credit_assessable_capital",
]
# council_tax_reduction_applicable_income on main before this change (1c5b4d04):
# these incomes and benefits, less income tax, National Insurance and half of
# pension contributions, floored at zero.
MAIN_INCOME_COMPONENTS = [
    "employment_income",
    "self_employment_income",
    "property_income",
    "private_pension_income",
    "carers_allowance",
    "esa_contrib",
    "jsa_contrib",
    "state_pension",
    "maternity_allowance",
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "ssmg",
    "tax_credits",
    "child_benefit",
    "income_support",
    "jsa_income",
    "esa_income",
    "universal_credit",
]
MAIN_DEDUCTIONS = ["income_tax", "national_insurance"]
HOUSEHOLD_VARIABLES = [
    "council_tax_reduction_maximum_eligible_liability",
    "council_tax_reduction_household_has_pensioner",
    "savings",
]


def guarantee_reform(single_weekly):
    if single_weekly is None:
        return None
    period = f"{YEAR}-01-01.{YEAR}-12-31"
    minimum_guarantee = "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee"
    return {
        f"{minimum_guarantee}.SINGLE": {period: single_weekly},
        f"{minimum_guarantee}.COUPLE": {period: single_weekly * 1.53},
    }


def calculate(units, guarantee=None, **kwargs):
    data, claimants = situation(units, **kwargs)
    sim = Simulation(situation=data, reform=guarantee_reform(guarantee))
    values = {
        v: np.asarray(sim.calculate(v, YEAR))[claimants] for v in BENUNIT_VARIABLES
    }
    # One household per family, in the same order as the claimant benefit units.
    for v in HOUSEHOLD_VARIABLES:
        values[v] = np.asarray(sim.calculate(v, YEAR))

    def benunit_total(names):
        return sum(
            np.asarray(sim.calculate(v, YEAR, map_to="benunit"))[claimants]
            for v in names
        )

    values["income_under_main_definition"] = np.maximum(
        0,
        benunit_total(MAIN_INCOME_COMPONENTS)
        - benunit_total(MAIN_DEDUCTIONS)
        - 0.5 * benunit_total(["pension_contributions"]),
    )
    values["national"] = np.array(
        [
            unit["country"] != "ENGLAND" or has_pensioner
            for unit, has_pensioner in zip(
                units, values["council_tax_reduction_household_has_pensioner"]
            )
        ]
    )
    return values


def tapered(liability, income, applicable_amount, non_dep):
    excess = max(0.0, income - applicable_amount)
    return max(0.0, liability - WITHDRAWAL_RATE * excess - non_dep)


def check_structural(values):
    ctr = values["simulated_council_tax_reduction_benunit"]
    liability = values["council_tax_reduction_maximum_eligible_liability"]
    gc = values["in_receipt_of_guarantee_credit"].astype(bool)
    sc_only = values["in_receipt_of_savings_credit_only"].astype(bool)
    received = gc | sc_only
    assert np.all(ctr >= 0)
    assert np.all(ctr <= liability + 0.01)
    assert not np.any(gc & sc_only)
    assert np.all(values["is_pension_credit_eligible"][received])
    assert np.all(values["would_claim_pc"][received])
    assert np.all(values["guarantee_credit"][gc] > 0)
    assert np.all(values["savings_credit"][sc_only] > 0)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=20, max_size=40), guarantees)
def test_awards_follow_the_pension_credit_routes(units, guarantee):
    check_routes(units, calculate(units, guarantee))


@PROPERTY_SETTINGS
@given(st.lists(savings_credit_families(), min_size=10, max_size=20))
def test_savings_credit_only_awards_use_the_pension_credit_assessment(units):
    values = calculate(units)
    assert values["in_receipt_of_savings_credit_only"].any()
    check_routes(units, values)


def check_routes(units, values):
    check_structural(values)
    for i, unit in enumerate(units):
        if not values["national"][i]:
            continue
        ctr = values["simulated_council_tax_reduction_benunit"][i]
        liability = values["council_tax_reduction_maximum_eligible_liability"][i]
        non_dep = values["council_tax_reduction_non_dep_deductions"][i]
        applicable_amount = values["council_tax_reduction_applicable_amount"][i]
        if values["in_receipt_of_guarantee_credit"][i]:
            expected = max(0.0, liability - non_dep)
            assert values["council_tax_reduction_applicable_income"][i] == 0, unit
        elif values["in_receipt_of_savings_credit_only"][i]:
            income = values["pension_credit_income"][i] + values["savings_credit"][i]
            assert (
                abs(values["council_tax_reduction_applicable_income"][i] - income)
                < 0.01
            ), unit
            expected = tapered(liability, income, applicable_amount, non_dep) * (
                values["pension_credit_assessable_capital"][i] <= CAPITAL_LIMIT
            )
        else:
            income = values["income_under_main_definition"][i]
            assert (
                abs(values["council_tax_reduction_applicable_income"][i] - income)
                < 0.01
            ), unit
            expected = tapered(liability, income, applicable_amount, non_dep) * (
                values["savings"][i] <= CAPITAL_LIMIT
            )
        assert abs(ctr - expected) < 0.01, (unit, ctr, expected)


@PROPERTY_SETTINGS
@given(
    populations,
    guarantees,
    st.floats(-3_000, 3_000, allow_nan=False, allow_infinity=False),
)
def test_guarantee_credit_recipients_ctr_is_invariant_to_state_pension(
    units, guarantee, change
):
    before = calculate(units, guarantee)
    after = calculate(units, guarantee, state_pension_change=change)
    assert before["in_receipt_of_guarantee_credit"].any()
    for i, unit in enumerate(units):
        if (
            before["in_receipt_of_guarantee_credit"][i]
            and after["in_receipt_of_guarantee_credit"][i]
        ):
            assert (
                abs(
                    before["simulated_council_tax_reduction_benunit"][i]
                    - after["simulated_council_tax_reduction_benunit"][i]
                )
                < 0.01
            ), (unit, change)


@PROPERTY_SETTINGS
@given(
    populations,
    guarantees,
    st.floats(0, 30_000, allow_nan=False, allow_infinity=False),
)
def test_guarantee_credit_recipients_ctr_is_invariant_to_savings(
    units, guarantee, change
):
    before = calculate(units, guarantee)
    after = calculate(units, guarantee, savings_change=change)
    assert before["in_receipt_of_guarantee_credit"].any()
    for i, unit in enumerate(units):
        if (
            before["in_receipt_of_guarantee_credit"][i]
            and after["in_receipt_of_guarantee_credit"][i]
        ):
            assert (
                abs(
                    before["simulated_council_tax_reduction_benunit"][i]
                    - after["simulated_council_tax_reduction_benunit"][i]
                )
                < 0.01
            ), (unit, change)


@PROPERTY_SETTINGS
@given(populations, guarantees)
def test_not_claiming_pension_credit_never_raises_a_recipients_ctr(units, guarantee):
    claiming = calculate(units, guarantee, would_claim_pc=True)
    not_claiming = calculate(units, guarantee, would_claim_pc=False)
    assert claiming["in_receipt_of_guarantee_credit"].any()
    assert not np.any(not_claiming["in_receipt_of_guarantee_credit"])
    check_routes(units, not_claiming)
    for i, unit in enumerate(units):
        if claiming["in_receipt_of_guarantee_credit"][i]:
            assert (
                not_claiming["simulated_council_tax_reduction_benunit"][i]
                <= claiming["simulated_council_tax_reduction_benunit"][i] + 0.01
            ), unit


def test_savings_credit_only_award_counts_the_frozen_savings_credit():
    # A savings credit rate rise raises the reform's savings credit from
    # 558.62 to 869.89, but the freeze keeps paying the baseline 558.62, and
    # that is the savings credit payable.
    person = {
        "age": {YEAR: 90},
        "state_pension": {YEAR: 12_000},
        "private_pension_income": {YEAR: 1_500},
    }
    data = {
        "people": {"pensioner": person},
        "benunits": {
            "benunit": {
                "members": ["pensioner"],
                "claims_all_entitled_benefits": {YEAR: True},
            }
        },
        "households": {
            "household": {
                "members": ["pensioner"],
                "country": {YEAR: "ENGLAND"},
                "local_authority": {YEAR: "MAIDSTONE"},
                "tenure_type": {YEAR: "OWNED_OUTRIGHT"},
                "council_tax": {YEAR: 2_000},
                "savings": {YEAR: 0},
            }
        },
    }
    period = f"{YEAR}-01-01.{YEAR}-12-31"
    rate_rise = {"gov.dwp.pension_credit.savings_credit.rate.phase_in": {period: 0.8}}
    frozen = Simulation(
        situation=data,
        reform={**rate_rise, "gov.contrib.freeze_pension_credit": {period: True}},
    )
    unfrozen = Simulation(situation=data, reform=rate_rise)
    assert abs(frozen.calculate("savings_credit", YEAR)[0] - 869.89) < 0.01
    assert abs(frozen.calculate("pension_credit", YEAR)[0] - 558.62) < 0.01
    assert frozen.calculate("in_receipt_of_savings_credit_only", YEAR)[0]
    # 13,314 Pension Credit income + 558.62 paid; 2,000 - 0.2 x 560.62.
    frozen_income = frozen.calculate("council_tax_reduction_applicable_income", YEAR)
    assert abs(frozen_income[0] - 13_872.62) < 0.01
    assert abs(frozen.calculate("council_tax_reduction", YEAR)[0] - 1_887.88) < 0.01
    # Without the freeze the higher savings credit is paid and counted.
    unfrozen_income = unfrozen.calculate(
        "council_tax_reduction_applicable_income", YEAR
    )
    assert abs(unfrozen_income[0] - 14_183.89) < 0.01


def freeze_case(age, state_pension, private_pension, savings, reform):
    person = {
        "age": {YEAR: age},
        "state_pension": {YEAR: state_pension},
        "private_pension_income": {YEAR: private_pension},
    }
    data = {
        "people": {"pensioner": person},
        "benunits": {
            "benunit": {
                "members": ["pensioner"],
                "claims_all_entitled_benefits": {YEAR: True},
            }
        },
        "households": {
            "household": {
                "members": ["pensioner"],
                "country": {YEAR: "ENGLAND"},
                "local_authority": {YEAR: "MAIDSTONE"},
                "tenure_type": {YEAR: "OWNED_OUTRIGHT"},
                "council_tax": {YEAR: 2_000},
                "savings": {YEAR: savings},
            }
        },
    }
    period = f"{YEAR}-01-01.{YEAR}-12-31"
    reform = {key: {period: value} for key, value in reform.items()}
    frozen = Simulation(
        situation=data,
        reform={**reform, "gov.contrib.freeze_pension_credit": {period: True}},
    )
    unfrozen = Simulation(situation=data, reform=reform)
    return frozen, unfrozen


def test_freeze_keeps_savings_credit_only_receipt_when_the_reform_adds_guarantee_credit():
    # A higher guarantee gives the reform a guarantee credit, but the frozen
    # award is the baseline's savings credit of 558.62.
    frozen, unfrozen = freeze_case(
        90,
        12_000,
        1_500,
        0,
        {"gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.SINGLE": 300},
    )
    assert unfrozen.calculate("in_receipt_of_guarantee_credit", YEAR)[0]
    assert abs(unfrozen.calculate("council_tax_reduction", YEAR)[0] - 2_000) < 0.01
    assert not frozen.calculate("in_receipt_of_guarantee_credit", YEAR)[0]
    assert frozen.calculate("in_receipt_of_savings_credit_only", YEAR)[0]
    # 2,000 - 0.2 x (13,314 + 558.62 - 13,312)
    assert abs(frozen.calculate("council_tax_reduction", YEAR)[0] - 1_887.88) < 0.01


def test_freeze_keeps_guarantee_credit_receipt_when_the_reform_removes_it():
    # With no minimum guarantee the reform pays no guarantee credit, so the
    # 20,000 savings exceed the capital limit; the frozen award is still the
    # baseline guarantee credit, so capital is disregarded.
    frozen, unfrozen = freeze_case(
        70,
        9_000,
        0,
        20_000,
        {"gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.SINGLE": 0},
    )
    assert not unfrozen.calculate("in_receipt_of_guarantee_credit", YEAR)[0]
    assert unfrozen.calculate("council_tax_reduction", YEAR)[0] == 0
    assert frozen.calculate("in_receipt_of_guarantee_credit", YEAR)[0]
    assert abs(frozen.calculate("council_tax_reduction", YEAR)[0] - 2_000) < 0.01
