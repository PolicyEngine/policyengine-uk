"""Property-based tests for receipt of a savings-credit-only Pension Credit award.

State pension credit "shall be payable in accordance with the following
provisions of this Act" (SPCA 2002 s.1(1)), as a guarantee credit, a savings
credit, or both (s.1(3)). The pensioner Council Tax Reduction schemes and
pension-age Housing Benefit use the Secretary of State's assessment of income
and capital for a person "who has, or whose partner has, an award of state
pension credit comprising only the savings credit" (SI 2012/2885 Sch 1 para
14(1); SI 2006/214 reg 27(1)), adjusted for the savings credit payable (para
14(2)(a); reg 27(4)(a)). `in_receipt_of_savings_credit_only` is the model's
test for that award.

Two versions of the test are compared:

- main: the benefit unit is eligible for Pension Credit, claims it, has a
  positive savings credit and no guarantee credit (under the Pension Credit
  freeze: the baseline receipt). It does not ask whether Pension Credit is
  paid, so a reform that stops Pension Credit being paid leaves the family
  assessed on an award it no longer has;
- fix: the same, and Pension Credit is paid, on both paths.

Invariants, for any generated population of pension-age, mixed-age and
working-age families, owners and council tenants:

1. Differential: in the unreformed model the fix changes nothing. Pension
   Credit paid is the entitlement (guarantee credit plus savings credit) of a
   family that claims, so main's conditions already imply a payment. Receipt
   and every output that reads it are the same under main and the fix.
2. Receipt implies payment: in every scenario below, a family in receipt of
   savings credit only is paid Pension Credit and is not in receipt of a
   guarantee credit; in the unreformed model it is also eligible, claims, has
   a positive savings credit and no guarantee credit.
3. Payment: a reform that stops Pension Credit being paid ends receipt for
   every family, with or without the Pension Credit freeze. Fails for main.
4. Metamorphic: with Pension Credit not paid, a family not in receipt of a
   guarantee credit is assessed for Council Tax Reduction and Housing Benefit
   exactly as if it did not claim Pension Credit. Fails for main. (Families
   in receipt of a guarantee credit are left out because main's
   `in_receipt_of_guarantee_credit` does not yet need a payment; #1987 adds
   it.)
5. Freeze: under the Pension Credit freeze alone, receipt is the baseline
   receipt whatever the reform does to the computed credits, under main and
   the fix alike.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import YEAR as YEAR_PERIOD
from policyengine_uk.model_api import BenUnit, Variable
from policyengine_uk.utils.scenario import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=6,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Local authorities without a modelled local council tax reduction scheme, so
# each country's national scheme (England: pensioners only) applies.
COUNTRIES = {
    "ENGLAND": "MAIDSTONE",
    "WALES": "CARDIFF",
    "SCOTLAND": "GLASGOW_CITY",
}
# Savings credit needs State Pension age reached before 6 April 2016, so
# aged 80 or over in 2026 is safely inside and 67 to 76 is over State
# Pension age but outside.
SAVINGS_CREDIT_AGE = st.integers(80, 100)
PENSION_AGE = st.one_of(st.integers(67, 76), SAVINGS_CREDIT_AGE)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single_pension": [PENSION_AGE],
    "couple_pension": [PENSION_AGE, PENSION_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
    "single_working": [WORKING_AGE],
}
FLAG = "in_receipt_of_savings_credit_only"
# Every output that reads the flag, and the awards they feed.
CONSUMERS = [
    "council_tax_reduction_applicable_income",
    "council_tax_reduction_assessable_capital",
    "simulated_council_tax_reduction_benunit",
    "housing_benefit_applicable_income",
    "housing_benefit_assessable_capital",
    "housing_benefit_tariff_income",
    "housing_benefit",
]
VARIABLES = [
    FLAG,
    "in_receipt_of_guarantee_credit",
    "is_pension_credit_eligible",
    "would_claim_pc",
    "guarantee_credit",
    "savings_credit",
    "pension_credit",
] + CONSUMERS
BOOLEANS = [
    FLAG,
    "in_receipt_of_guarantee_credit",
    "is_pension_credit_eligible",
    "would_claim_pc",
]
FREEZE = {"gov.contrib.freeze_pension_credit": True}
MINIMUM_GUARANTEE = "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee"
# Reforms that change which credit the reform alone would compute.
CREDIT_REFORMS = [
    # A savings credit rate rise: more savings credit.
    {"gov.dwp.pension_credit.savings_credit.rate.phase_in": 0.8},
    # A higher guarantee: savings-credit-only families gain a guarantee credit.
    {f"{MINIMUM_GUARANTEE}.SINGLE": 300, f"{MINIMUM_GUARANTEE}.COUPLE": 459},
    # No guarantee: guarantee credit recipients lose it.
    {f"{MINIMUM_GUARANTEE}.SINGLE": 0, f"{MINIMUM_GUARANTEE}.COUPLE": 0},
]


def money(low, high):
    return st.floats(low, high, allow_nan=False, allow_infinity=False)


@st.composite
def families(draw):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    return dict(
        ages=[draw(age) for age in SHAPES[shape]],
        country=draw(st.sampled_from(sorted(COUNTRIES))),
        rent=draw(st.one_of(st.none(), money(3_000, 12_000))),
        council_tax=draw(money(500, 4_000)),
        savings=draw(st.one_of(st.just(0.0), money(0, 30_000))),
        other_property=draw(st.one_of(st.just(0.0), money(0, 10_000))),
        # Half the draws fall around the minimum guarantee, where guarantee
        # credit and savings credit meet.
        state_pension=draw(st.one_of(money(0, 25_000), money(10_000, 16_000))),
        private_pension=draw(st.one_of(st.just(0.0), money(0, 5_000))),
        earnings=draw(st.one_of(st.just(0.0), money(0, 20_000))),
        would_claim_pc=draw(st.sampled_from([True, True, False])),
    )


@st.composite
def savings_credit_families(draw):
    """Single pensioners who reached State Pension age before April 2016
    with income just above the minimum guarantee, the savings credit range."""
    return dict(
        ages=[draw(SAVINGS_CREDIT_AGE)],
        country=draw(st.sampled_from(sorted(COUNTRIES))),
        rent=draw(st.one_of(st.none(), money(3_000, 12_000))),
        council_tax=draw(money(500, 4_000)),
        savings=draw(st.one_of(st.just(0.0), money(0, 25_000))),
        other_property=draw(st.one_of(st.just(0.0), money(0, 10_000))),
        state_pension=draw(money(12_400, 14_500)),
        private_pension=0.0,
        earnings=0.0,
        would_claim_pc=True,
    )


def family(ages, **overrides):
    unit = dict(
        ages=ages,
        country="ENGLAND",
        rent=None,
        council_tax=2_000.0,
        savings=0.0,
        other_property=0.0,
        state_pension=0.0,
        private_pension=0.0,
        earnings=0.0,
        would_claim_pc=True,
    )
    unit.update(overrides)
    return unit


# The savings-credit-only pensioner of the fixed examples, and the same
# pensioner with capital, renting, and not claiming; a guarantee credit
# recipient; and a working-age family.
KNOWN_FAMILIES = [
    family([90], state_pension=12_480.0),
    family([90], state_pension=12_480.0, savings=12_000.0, other_property=5_000.0),
    family([90], state_pension=12_480.0, savings=12_000.0, rent=6_000.0),
    family([90], state_pension=12_480.0, would_claim_pc=False),
    family([70], state_pension=9_000.0),
    family([30], earnings=15_000.0),
]
SAVINGS_CREDIT_ONLY = [True, True, True, False, False, False]
OWNER_WITH_CAPITAL, TENANT = 1, 2
populations = st.builds(
    lambda random, recipients: KNOWN_FAMILIES + random + recipients,
    st.lists(families(), min_size=8, max_size=16),
    st.lists(savings_credit_families(), min_size=3, max_size=6),
)


def situation(units, would_claim_pc=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            # The generated adults are the claimant and partner (a mixed-age
            # couple may pair 67 with 18); say so, so the claimant-or-partner
            # presumption does not apply.
            person = {"age": {YEAR: age}, "is_claimant_or_partner": {YEAR: True}}
            if age >= 67:
                person["state_pension"] = {YEAR: unit["state_pension"]}
                person["private_pension_income"] = {YEAR: unit["private_pension"]}
            else:
                person["employment_income"] = {YEAR: unit["earnings"]}
            people[name] = person
            names.append(name)
        claims = unit["would_claim_pc"] if would_claim_pc is None else would_claim_pc
        benunits[f"b{i}"] = {
            "members": names,
            # claims_all_entitled_benefits sums reported benefits across the
            # whole simulation, so set it for every family.
            "claims_all_entitled_benefits": {YEAR: True},
            "would_claim_pc": {YEAR: claims},
            "would_claim_uc": {YEAR: False},
        }
        rents = unit["rent"] is not None
        households[f"h{i}"] = {
            "members": names,
            "country": {YEAR: unit["country"]},
            "local_authority": {YEAR: COUNTRIES[unit["country"]]},
            "tenure_type": {YEAR: "RENT_FROM_COUNCIL" if rents else "OWNED_OUTRIGHT"},
            "rent": {YEAR: unit["rent"] if rents else 0.0},
            "council_tax": {YEAR: unit["council_tax"]},
            "savings": {YEAR: unit["savings"]},
            "other_residential_property_value": {YEAR: unit["other_property"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def main_formula(benunit, period, parameters):
    # in_receipt_of_savings_credit_only on main before this change (3f174d07).
    freeze = parameters(period).gov.contrib.freeze_pension_credit
    baseline = benunit.simulation.baseline
    if freeze and baseline is not None:
        return baseline.populations["benunit"](FLAG, period)
    eligible = benunit("is_pension_credit_eligible", period)
    would_claim = benunit("would_claim_pc", period)
    guarantee_credit = benunit("guarantee_credit", period)
    savings_credit = benunit("savings_credit", period)
    return eligible & would_claim & (guarantee_credit <= 0) & (savings_credit > 0)


MAIN = type(
    FLAG,
    (Variable,),
    dict(
        value_type=bool,
        entity=BenUnit,
        definition_period=YEAR_PERIOD,
        label="in receipt of Savings Credit only (main)",
        formula=main_formula,
    ),
)


def stop_pension_credit(sim):
    sim.tax_benefit_system.neutralize_variable("pension_credit")


def scenario(parameter_changes=None, stopped=False):
    if parameter_changes is None and not stopped:
        return None
    return Scenario(
        parameter_changes=parameter_changes,
        simulation_modifier=stop_pension_credit if stopped else None,
    )


def calculate(
    units, version="fix", parameter_changes=None, stopped=False, would_claim_pc=None
):
    sim = Simulation(
        situation=situation(units, would_claim_pc=would_claim_pc),
        scenario=scenario(parameter_changes, stopped),
    )
    if version == "main":
        sim.tax_benefit_system.update_variable(MAIN)
    values = {v: np.asarray(sim.calculate(v, YEAR)) for v in VARIABLES}
    for name in BOOLEANS:
        values[name] = values[name].astype(bool)
    return values


def check_receipt_implies_payment(values):
    receipt = values[FLAG]
    assert np.all(values["pension_credit"][receipt] > 0)
    assert not np.any(receipt & values["in_receipt_of_guarantee_credit"])


def assessed_differently(a, b, where):
    """Outputs that differ between two runs for the selected families."""
    return [
        name
        for name in [FLAG] + CONSUMERS
        if not np.allclose(
            a[name][where].astype(float), b[name][where].astype(float), atol=0.01
        )
    ]


@PROPERTY_SETTINGS
@given(populations)
def test_fix_changes_nothing_in_the_unreformed_model(units):
    fix = calculate(units)
    main = calculate(units, version="main")
    everyone = np.ones(len(units), dtype=bool)
    assert np.array_equal(fix[FLAG], main[FLAG])
    assert assessed_differently(fix, main, everyone) == []
    for name in VARIABLES:
        assert np.array_equal(fix[name], main[name]), name
    # Receipt is the same test main applied, and it implies a payment.
    receipt = fix[FLAG]
    assert np.array_equal(
        receipt,
        fix["is_pension_credit_eligible"]
        & fix["would_claim_pc"]
        & (fix["guarantee_credit"] <= 0)
        & (fix["savings_credit"] > 0),
    )
    check_receipt_implies_payment(fix)
    # The paid award of a savings-credit-only family is its savings credit.
    assert np.allclose(
        fix["pension_credit"][receipt], fix["savings_credit"][receipt], atol=0.01
    )
    # Not vacuous: the known savings-credit-only families are in receipt.
    assert receipt[: len(KNOWN_FAMILIES)].tolist() == SAVINGS_CREDIT_ONLY


@PROPERTY_SETTINGS
@given(populations)
def test_stopping_pension_credit_payments_ends_receipt(units):
    stopped = calculate(units, stopped=True)
    frozen_and_stopped = calculate(units, parameter_changes=FREEZE, stopped=True)
    not_claiming = calculate(units, would_claim_pc=False)
    for values in [stopped, frozen_and_stopped, not_claiming]:
        assert not np.any(values["pension_credit"] > 0)
        assert not np.any(values[FLAG])
        check_receipt_implies_payment(values)
    # The savings credit is still computed; it is just not paid.
    known = np.array(SAVINGS_CREDIT_ONLY)
    assert np.all(stopped["savings_credit"][: len(KNOWN_FAMILIES)][known] > 0)
    # A family whose Pension Credit is not paid is assessed like one that
    # does not claim it, unless main still reads it as on guarantee credit.
    for values in [stopped, frozen_and_stopped]:
        no_guarantee_credit = ~values["in_receipt_of_guarantee_credit"]
        assert no_guarantee_credit[: len(KNOWN_FAMILIES)][known].all()
        assert assessed_differently(values, not_claiming, no_guarantee_credit) == []


@PROPERTY_SETTINGS
@given(populations, st.sampled_from(CREDIT_REFORMS))
def test_pension_credit_freeze_keeps_the_baseline_receipt(units, credit_reform):
    unreformed = calculate(units)
    frozen = calculate(units, parameter_changes={**credit_reform, **FREEZE})
    frozen_main = calculate(
        units, version="main", parameter_changes={**credit_reform, **FREEZE}
    )
    assert np.array_equal(frozen[FLAG], unreformed[FLAG])
    assert np.array_equal(frozen[FLAG], frozen_main[FLAG])
    # The frozen award is the baseline award.
    assert np.allclose(frozen["pension_credit"], unreformed["pension_credit"])
    check_receipt_implies_payment(frozen)
    everyone = np.ones(len(units), dtype=bool)
    assert assessed_differently(frozen, frozen_main, everyone) == []


def test_known_families_detect_main():
    # The properties are not vacuous: main breaks invariants 3 and 4 on the
    # known families, and the fix does not.
    known = np.array(SAVINGS_CREDIT_ONLY)
    not_claiming = calculate(KNOWN_FAMILIES, would_claim_pc=False)
    for parameter_changes in [None, FREEZE]:
        main = calculate(
            KNOWN_FAMILIES,
            version="main",
            parameter_changes=parameter_changes,
            stopped=True,
        )
        assert not np.any(main["pension_credit"] > 0)
        assert main[FLAG].tolist() == SAVINGS_CREDIT_ONLY
        fix = calculate(
            KNOWN_FAMILIES, parameter_changes=parameter_changes, stopped=True
        )
        assert not np.any(fix[FLAG])
        # Main keeps the Pension Credit assessment. The owner with capital is
        # tested on 17,000 against the 16,000 limit and gets no council tax
        # reduction, where the scheme's own rules give 2,000 on savings of
        # 12,000. The tenant has no Housing Benefit tariff income, where
        # Housing Benefit's own rules count 4 a week on savings of 12,000
        # (208). Its Housing Benefit income is the same on both routes: with
        # no savings credit paid, the Pension Credit assessment is the State
        # Pension plus the same 208 of deemed income.
        assert assessed_differently(main, not_claiming, known) == [
            FLAG,
            "council_tax_reduction_applicable_income",
            "council_tax_reduction_assessable_capital",
            "simulated_council_tax_reduction_benunit",
            "housing_benefit_tariff_income",
        ]
        reduction = "simulated_council_tax_reduction_benunit"
        assert main[reduction][OWNER_WITH_CAPITAL] == 0
        assert abs(fix[reduction][OWNER_WITH_CAPITAL] - 2_000) < 0.01
        assert main["housing_benefit_tariff_income"][TENANT] == 0
        assert abs(fix["housing_benefit_tariff_income"][TENANT] - 208) < 0.01
        assert assessed_differently(fix, not_claiming, known) == []


def single_pensioner(savings=0.0, other_property=0.0):
    # Single, aged 90, State Pension 12,480 (240 a week), owning in Maidstone
    # with council tax of 2,000.
    return {
        "people": {"pensioner": {"age": {YEAR: 90}, "state_pension": {YEAR: 12_480}}},
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
                "other_residential_property_value": {YEAR: other_property},
            }
        },
    }


def test_stopping_pension_credit_payments_ends_savings_credit_only_receipt():
    data = single_pensioner()

    def read(simulation, variable):
        return float(simulation.calculate(variable, YEAR)[0])

    # Unreformed. The 2026 weekly rates are a standard minimum guarantee of
    # 238.00 and a savings credit threshold of 208.07, so the savings credit
    # is 0.6 x (238.00 - 208.07) - 0.4 x (240.00 - 238.00) = 17.158 a week, or
    # 892.22 a year, and there is no guarantee credit.
    unreformed = Simulation(situation=data)
    assert read(unreformed, "guarantee_credit") == 0
    assert abs(read(unreformed, "savings_credit") - 892.22) < 0.01
    assert abs(read(unreformed, "pension_credit") - 892.22) < 0.01
    assert unreformed.calculate(FLAG, YEAR).tolist() == [True]
    # Council tax reduction counts the Pension Credit income plus the savings
    # credit: 12,480 + 892.22 = 13,372.22, against an applicable amount of
    # 256.00 a week (13,312). 2,000 - 0.2 x 60.22 = 1,987.96.
    assert (
        abs(read(unreformed, "council_tax_reduction_applicable_income") - 13_372.22)
        < 0.01
    )
    assert abs(read(unreformed, "council_tax_reduction") - 1_987.96) < 0.01

    # A reform that stops Pension Credit being paid leaves the savings credit
    # computed but ends receipt, so the State Pension is assessed under the
    # scheme's own rules: 12,480 is below the applicable amount.
    stopped = Simulation(situation=data, scenario=scenario(stopped=True))
    assert abs(read(stopped, "savings_credit") - 892.22) < 0.01
    assert read(stopped, "pension_credit") == 0
    assert stopped.calculate(FLAG, YEAR).tolist() == [False]
    assert abs(read(stopped, "council_tax_reduction_applicable_income") - 12_480) < 0.01
    assert abs(read(stopped, "council_tax_reduction") - 2_000) < 0.01

    # The same holds with Pension Credit frozen: the frozen award is not paid
    # either, so the baseline receipt does not carry over.
    frozen_and_stopped = Simulation(
        situation=data, scenario=scenario(parameter_changes=FREEZE, stopped=True)
    )
    assert read(frozen_and_stopped, "pension_credit") == 0
    assert frozen_and_stopped.calculate(FLAG, YEAR).tolist() == [False]
    assert (
        abs(
            read(frozen_and_stopped, "council_tax_reduction_applicable_income") - 12_480
        )
        < 0.01
    )

    # The freeze alone keeps paying the baseline award, and with it receipt.
    frozen = Simulation(situation=data, scenario=scenario(parameter_changes=FREEZE))
    assert abs(read(frozen, "pension_credit") - 892.22) < 0.01
    assert frozen.calculate(FLAG, YEAR).tolist() == [True]


def test_stopping_pension_credit_payments_ends_the_pension_credit_capital_test():
    # Savings of 12,000 and other property worth 5,000. The Pension Credit
    # assessment of capital counts both (17,000), above the 16,000 limit, so
    # the savings-credit-only award leaves no council tax reduction. Deemed
    # income is 1 a week for each 500 over 10,000: 14 a week, so the savings
    # credit is 0.6 x 29.93 - 0.4 x (254.00 - 238.00) = 11.558 a week (601.02).
    data = single_pensioner(savings=12_000.0, other_property=5_000.0)
    unreformed = Simulation(situation=data)
    assert abs(unreformed.calculate("savings_credit", YEAR)[0] - 601.02) < 0.01
    assert unreformed.calculate(FLAG, YEAR).tolist() == [True]
    capital = "council_tax_reduction_assessable_capital"
    assert unreformed.calculate(capital, YEAR)[0] == 17_000
    assert unreformed.calculate("council_tax_reduction", YEAR)[0] == 0

    # With Pension Credit not paid the scheme's own capital rule applies, for
    # which household savings (12,000) stand in, within the limit.
    stopped = Simulation(situation=data, scenario=scenario(stopped=True))
    assert stopped.calculate(FLAG, YEAR).tolist() == [False]
    assert stopped.calculate(capital, YEAR)[0] == 12_000
    assert abs(stopped.calculate("council_tax_reduction", YEAR)[0] - 2_000) < 0.01
