"""Property-based tests for the universal credit limb of the Housing Benefit
passport.

SI 2006/213 Sch 4 para 12, Sch 5 para 4 and Sch 6 para 5 (NI: SR 2006/405
Sch 5 para 12, Sch 6 para 4 and Sch 7 para 5) disregard the earnings, the
whole income and the whole capital of a claimant on universal credit, as for
one on income support, income-based JSA or income-related ESA. A person is on
universal credit on any day they are entitled to it, whether it is in payment
or not (reg 2(3B)); the model reads Universal Credit before the benefit cap
and deductions. Housing Benefit is then the appropriate maximum: the eligible
rent, capped at the LHA rate for LHA tenants, less non-dependant deductions
(SSCBA 1992 s.130(3)(a); reg 70).

The model has no route yet to Housing Benefit alongside Universal Credit
(specified or temporary accommodation, UC (Transitional Provisions) Regs 2014
reg 5(2)(a)), so each claimant benefit unit supplies housing_benefit_eligible.

Invariants, for any generated population of renting families (some with a
non-dependant in the household), each on Universal Credit (a supplied amount
before the cap, or one the model computes), not on it, or on a legacy benefit:

1. Definition: housing_benefit_on_passporting_benefit is true exactly when
   Income Support, income-based JSA or income-related ESA is positive, or the
   family claims Universal Credit and its amount before the cap is positive.
2. Passport: a passported family has nil applicable income, assessable capital
   and tariff income; its earnings disregard is its net earnings; and its
   entitlement is exactly the maximum Housing Benefit. Every family's
   entitlement is at most that maximum.
3. Metamorphic: for a family on Universal Credit, raising its earnings,
   pensions and savings changes neither the passport nor its entitlement.
4. Differential: the universal credit limb and the Income Support limb give
   the same Housing Benefit means test.
5. Monotonic: putting a family on Universal Credit never lowers its Housing
   Benefit before the cap or its eligibility. (After the cap it can: Universal
   Credit counts towards the cap. The test reads the pre-cap amount.)
6. Dates: the universal credit limb applies in every model year from 2014 in
   Great Britain and from 2019 in Northern Ireland (in force 28 October 2013
   and 8 May 2018; model years are read on 30 April), and never before.
7. Order independence: with Housing Benefit and Universal Credit both paid,
   calculating Housing Benefit, Universal Credit, the benefit cap or the
   passport first gives the same results, so the passport (which reads
   Universal Credit before the cap) adds no circular dependency.
"""

import itertools

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.system import system

YEAR = 2025
PROPERTY_SETTINGS = settings(
    max_examples=5,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# State Pension age is 66 until 2026-27; 67 and over is unambiguously pension
# age and 60 and under unambiguously working age. A family whose members are
# all over pension age cannot claim Universal Credit, so there is no such
# shape here.
PENSION_AGE = st.integers(67, 90)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single_working": ([WORKING_AGE], 0),
    "couple_working": ([WORKING_AGE, WORKING_AGE], 0),
    "lone_parent": ([WORKING_AGE], 2),
    "couple_with_children": ([WORKING_AGE, WORKING_AGE], 1),
    "mixed_age": ([PENSION_AGE, WORKING_AGE], 0),
}
RENTING_TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY"]
LEGACY = ["income_support", "jsa_income", "esa_income"]
COUNTRIES = ["ENGLAND", "SCOTLAND", "WALES", "NORTHERN_IRELAND"]
money = st.floats(0, 20_000, allow_nan=False, allow_infinity=False)
# A supplied Universal Credit amount before the cap: nil, the one-penny
# minimum, or more.
uc_amount = st.one_of(
    st.just(0.0), st.just(0.01), st.floats(1, 15_000, allow_nan=False)
)


@st.composite
def families(draw, uc_modes=("off", "supplied", "computed"), legacy=True):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    ages, n_children = SHAPES[shape]
    mode = draw(st.sampled_from(uc_modes))
    # At most one legacy benefit, and none for half the families, so that
    # most families on Universal Credit are passported by it alone.
    legacy_benefit = draw(st.sampled_from([None] * 3 + LEGACY)) if legacy else None
    legacy_amount = draw(st.floats(1, 12_000, allow_nan=False))
    return dict(
        adults=[
            dict(
                age=draw(age),
                employment_income=draw(st.one_of(st.just(0.0), money)),
                private_pension_income=draw(st.one_of(st.just(0.0), money)),
            )
            for age in ages
        ],
        children=[draw(st.integers(0, 15)) for _ in range(n_children)],
        tenure=draw(st.sampled_from(RENTING_TENURES)),
        country=draw(st.sampled_from(COUNTRIES)),
        rent=draw(money),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
        uc_mode=mode,
        uc_amount=draw(uc_amount) if mode == "supplied" else None,
        legacy={
            benefit: legacy_amount if benefit == legacy_benefit else 0.0
            for benefit in LEGACY
        },
        non_dependant_earnings=draw(st.one_of(st.none(), st.floats(0, 40_000))),
    )


# Appended to every generated population, so that each example has a family
# passported by Universal Credit alone, with earnings and capital the passport
# must disregard.
ON_UNIVERSAL_CREDIT_ONLY = dict(
    adults=[dict(age=40, employment_income=8_000.0, private_pension_income=0.0)],
    children=[],
    tenure="RENT_FROM_COUNCIL",
    country="ENGLAND",
    rent=5_200.0,
    savings=12_000.0,
    uc_mode="supplied",
    uc_amount=1_000.0,
    legacy={benefit: 0.0 for benefit in LEGACY},
    non_dependant_earnings=None,
)


def situation(units, bump=0.0, overrides=None):
    """Build one claimant benefit unit per family, first in its household,
    followed by any non-dependant's own benefit unit.

    bump raises every adult's earnings and pensions and the savings; overrides
    replaces fields of each family (for example its uc_mode or legacy amounts).
    """
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        unit = {**unit, **(overrides[i] if overrides else {})}
        members = []
        for j, adult in enumerate(unit["adults"]):
            name = f"a{i}_{j}"
            person = {
                "age": {YEAR: adult["age"]},
                "employment_income": {YEAR: adult["employment_income"] + bump},
                "private_pension_income": {
                    YEAR: adult["private_pension_income"] + bump
                },
            }
            if j == 0:
                person["housing_benefit_reported"] = {YEAR: 1.0}
            people[name] = person
            members.append(name)
        for k, child_age in enumerate(unit["children"]):
            name = f"c{i}_{k}"
            people[name] = {"age": {YEAR: child_age}}
            members.append(name)
        benunit = {
            "members": list(members),
            # Stands in for a claim in specified or temporary accommodation.
            "housing_benefit_eligible": {YEAR: True},
            # Pension Credit's guarantee credit passports a pension-age
            # family in its own right; hold it at nil to isolate this one.
            "guarantee_credit": {YEAR: 0.0},
            **{benefit: {YEAR: unit["legacy"][benefit]} for benefit in LEGACY},
        }
        if unit["uc_mode"] == "off":
            benunit["would_claim_uc"] = {YEAR: False}
        else:
            benunit["would_claim_uc"] = {YEAR: True}
            if unit["uc_mode"] == "supplied":
                benunit["universal_credit_pre_benefit_cap"] = {YEAR: unit["uc_amount"]}
        benunits[f"b{i}"] = benunit
        household_members = list(members)
        if unit["non_dependant_earnings"] is not None:
            name = f"n{i}"
            people[name] = {
                "age": {YEAR: 30},
                "employment_income": {YEAR: unit["non_dependant_earnings"]},
            }
            benunits[f"nb{i}"] = {"members": [name], "would_claim_uc": {YEAR: False}}
            household_members.append(name)
        households[f"h{i}"] = {
            "members": household_members,
            "country": {YEAR: unit["country"]},
            "tenure_type": {YEAR: unit["tenure"]},
            "rent": {YEAR: unit["rent"]},
            "savings": {YEAR: unit["savings"] + bump},
        }
    return {"people": people, "benunits": benunits, "households": households}


VARIABLES = [
    "housing_benefit_on_passporting_benefit",
    "in_receipt_of_income_support_jsa_ib_or_esa_ir",
    "is_uc_entitled",
    "would_claim_uc",
    "universal_credit_pre_benefit_cap",
    "housing_benefit_net_earnings",
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_applicable_income",
    "housing_benefit_assessable_capital",
    "housing_benefit_tariff_income",
    "housing_benefit_entitlement",
    "housing_benefit_eligible",
    "housing_benefit_pre_benefit_cap",
    "housing_benefit_non_dep_deductions",
    "benunit_rent",
    "LHA_eligible",
    "LHA_cap",
]
MEANS_TEST = [
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_applicable_income",
    "housing_benefit_assessable_capital",
    "housing_benefit_tariff_income",
    "housing_benefit_entitlement",
]


def calculate(units, order=None, **kwargs):
    sim = Simulation(situation=situation(units, **kwargs))
    for variable in order or []:
        sim.calculate(variable, YEAR)
    values = {v: np.asarray(sim.calculate(v, YEAR)) for v in VARIABLES}
    benunit_ids = list(sim.populations["benunit"].ids)
    claimants = [benunit_ids.index(f"b{i}") for i in range(len(units))]
    return {k: v[claimants] for k, v in values.items()}


def maximum_housing_benefit(values):
    rent = values["benunit_rent"]
    lha = values["LHA_eligible"].astype(bool)
    capped_rent = np.where(lha, np.minimum(rent, values["LHA_cap"]), rent)
    return np.maximum(0, capped_rent - values["housing_benefit_non_dep_deductions"])


def passported(values):
    return values["housing_benefit_on_passporting_benefit"].astype(bool)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=20))
def test_definition_passport_and_maximum(units):
    units = units + [ON_UNIVERSAL_CREDIT_ONLY]
    values = calculate(units)
    passport = passported(values)
    # 1. Definition.
    legacy = np.array([any(u["legacy"][b] > 0 for b in LEGACY) for u in units])
    claims_uc = values["would_claim_uc"].astype(bool)
    on_uc = claims_uc & (values["universal_credit_pre_benefit_cap"] > 0)
    assert np.array_equal(values["is_uc_entitled"].astype(bool), on_uc)
    assert np.array_equal(passport, legacy | on_uc)
    # 2. Passport.
    for variable in [
        "housing_benefit_applicable_income",
        "housing_benefit_assessable_capital",
        "housing_benefit_tariff_income",
    ]:
        assert np.all(values[variable][passport] == 0), variable
    assert np.allclose(
        values["housing_benefit_applicable_income_disregard"][passport],
        values["housing_benefit_net_earnings"][passport],
        atol=0.01,
    )
    maximum = maximum_housing_benefit(values)
    entitlement = values["housing_benefit_entitlement"]
    assert np.all(entitlement <= maximum + 0.01)
    assert np.allclose(entitlement[passport], maximum[passport], atol=0.01)


@PROPERTY_SETTINGS
@given(
    st.lists(families(uc_modes=("supplied",), legacy=False), min_size=1, max_size=20),
    st.floats(1, 50_000, allow_nan=False),
)
def test_universal_credit_passport_ignores_income_and_capital(units, bump):
    units = units + [ON_UNIVERSAL_CREDIT_ONLY]
    before = calculate(units)
    after = calculate(units, bump=bump)
    passport = passported(before)
    # A supplied amount does not move with income, so neither does the
    # passport, which holds exactly where the amount is positive.
    amounts = np.array([unit["uc_amount"] for unit in units])
    assert np.array_equal(passport, amounts > 0)
    assert np.array_equal(passport, passported(after))
    for variable in ["housing_benefit_entitlement", "housing_benefit_eligible"]:
        assert np.allclose(
            before[variable][passport], after[variable][passport], atol=0.01
        ), variable


@PROPERTY_SETTINGS
@given(
    st.lists(families(legacy=False), min_size=1, max_size=20),
    st.floats(0.01, 15_000, allow_nan=False),
)
def test_universal_credit_and_income_support_limbs_agree(units, amount):
    no_legacy = {benefit: 0.0 for benefit in LEGACY}
    on_uc = calculate(
        units,
        overrides=[
            {"uc_mode": "supplied", "uc_amount": amount, "legacy": no_legacy}
            for _ in units
        ],
    )
    on_income_support = calculate(
        units,
        overrides=[
            {"uc_mode": "off", "legacy": {**no_legacy, "income_support": amount}}
            for _ in units
        ],
    )
    assert passported(on_uc).all()
    assert passported(on_income_support).all()
    assert not on_uc["in_receipt_of_income_support_jsa_ib_or_esa_ir"].any()
    for variable in MEANS_TEST:
        assert np.allclose(on_uc[variable], on_income_support[variable], atol=0.01), (
            variable
        )


@PROPERTY_SETTINGS
@given(
    st.lists(families(legacy=False), min_size=1, max_size=20),
    st.floats(0.01, 15_000, allow_nan=False),
)
def test_universal_credit_never_lowers_pre_cap_housing_benefit(units, amount):
    off = calculate(units, overrides=[{"uc_mode": "off"} for _ in units])
    on = calculate(
        units,
        overrides=[{"uc_mode": "supplied", "uc_amount": amount} for _ in units],
    )
    assert not passported(off).any()
    assert passported(on).all()
    assert np.all(
        on["housing_benefit_pre_benefit_cap"]
        >= off["housing_benefit_pre_benefit_cap"] - 0.01
    )
    assert np.all(
        on["housing_benefit_entitlement"] >= off["housing_benefit_entitlement"] - 0.01
    )
    assert np.all(on["housing_benefit_eligible"] >= off["housing_benefit_eligible"])


def test_universal_credit_limb_dates():
    in_force = {"great_britain": 2014, "northern_ireland": 2019}
    for year, country in itertools.product(range(2013, 2031), COUNTRIES):
        jurisdiction = (
            "northern_ireland" if country == "NORTHERN_IRELAND" else "great_britain"
        )
        sim = Simulation(
            situation={
                "people": {"p": {"age": {year: 40}}},
                "benunits": {
                    "b": {
                        "members": ["p"],
                        "is_uc_entitled": {year: True},
                        "in_receipt_of_income_support_jsa_ib_or_esa_ir": {year: False},
                    }
                },
                "households": {"h": {"members": ["p"], "country": {year: country}}},
            }
        )
        expected = year >= in_force[jurisdiction]
        result = sim.calculate("housing_benefit_on_passporting_benefit", year)[0]
        assert bool(result) == expected, (year, country)
        p = system.parameters(year).gov.dwp.housing_benefit.means_test
        assert bool(p.universal_credit_passport[jurisdiction]) == expected


@PROPERTY_SETTINGS
@given(
    st.lists(families(uc_modes=("computed",), legacy=False), min_size=1, max_size=10)
)
def test_calculation_order_does_not_change_results(units):
    orders = [
        ["housing_benefit"],
        ["universal_credit"],
        ["benefit_cap_reduction"],
        ["housing_benefit_on_passporting_benefit"],
        ["household_net_income"],
    ]
    results = [calculate(units, order=order) for order in orders]
    for other in results[1:]:
        for variable in VARIABLES:
            assert np.allclose(
                results[0][variable].astype(float),
                other[variable].astype(float),
                atol=0.01,
            ), variable
