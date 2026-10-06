"""Property-based tests for the Housing Benefit Guarantee Credit passport.

"In the case of a claimant who is in receipt, or whose partner is in receipt,
of a guarantee credit, the whole of his capital and income shall be
disregarded." (SI 2006/214 reg 26; NI: SR 2006/406 reg 24.) The passport
follows in_receipt_of_guarantee_credit: Pension Credit is paid and includes a
guarantee credit.

Invariants, for any generated population of families:

1. Receipt: in_receipt_of_guarantee_credit is true exactly when pension_credit
   and guarantee_credit are both positive, so it implies Pension Credit
   eligibility and would_claim_pc, and every claimant and partner in a
   receiving family (is_claimant_or_partner) is over State Pension age. A
   dependent 18 or 19 year old is not a partner, so it does not count.
2. Passport: a receiving family's Housing Benefit applicable income, tariff
   income and assessable capital are all zero.
3. Differential: where the family claims and is eligible for Pension Credit,
   every Housing Benefit output equals the pre-fix formula (passport on a
   computed guarantee credit). The two passports differ exactly for families
   with someone over State Pension age and a computed guarantee credit that is
   not paid; there the pre-fix formula passports and this one does not
   (intended). For a mixed-age couple saved by SI 2019/37 art 4, which
   is_pension_credit_eligible omits, that is a known departure from the law
   until the saving is modelled. Housing Benefit itself then differs only
   when the counted capital is over the limit or the counted income exceeds
   the applicable amount.
4. Metamorphic: not claiming Pension Credit never raises Housing Benefit.
5. Under the Pension Credit freeze, receipt is the baseline receipt, because
   the frozen award is the baseline award.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation
from policyengine_uk.model_api import YEAR as YEAR_PERIOD
from policyengine_uk.model_api import BenUnit, Variable

YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
TENURES = ["RENT_FROM_COUNCIL", "RENT_FROM_HA", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
# State Pension age is 66 until 2026-27 finishes phasing up; 67 and over is
# unambiguously pension age and 60 and under unambiguously working age.
PENSION_AGE = st.integers(67, 100)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single_pension": [PENSION_AGE],
    "couple_pension": [PENSION_AGE, PENSION_AGE],
    "mixed_age": [PENSION_AGE, WORKING_AGE],
    "single_working": [WORKING_AGE],
}
money = st.floats(0, 20_000, allow_nan=False, allow_infinity=False)


@st.composite
def families(draw):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    return dict(
        ages=[draw(age) for age in SHAPES[shape]],
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(money),
        savings=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
        state_pension=draw(money),
        private_pension=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
        would_claim_pc=draw(st.booleans()),
        hb_reported=draw(st.sampled_from([0.0, 1.0])),
    )


POPULATIONS = st.lists(families(), min_size=1, max_size=30)


def situation(units, would_claim_pc=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, age in enumerate(unit["ages"]):
            name = f"p{i}_{j}"
            person = {"age": {YEAR: age}}
            if age >= 67:
                person["state_pension_reported"] = {YEAR: unit["state_pension"]}
                person["private_pension_income"] = {YEAR: unit["private_pension"]}
            if j == 0 and unit["hb_reported"]:
                person["housing_benefit_reported"] = {YEAR: unit["hb_reported"]}
            people[name] = person
            names.append(name)
        claims = unit["would_claim_pc"] if would_claim_pc is None else would_claim_pc
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_pc": {YEAR: claims},
            "would_claim_uc": {YEAR: False},
        }
        households[f"h{i}"] = {
            "members": names,
            "rent": {YEAR: unit["rent"]},
            "tenure_type": {YEAR: unit["tenure"]},
            "savings": {YEAR: unit["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


class in_receipt_of_guarantee_credit(Variable):
    # The passport test on main before this fix: a computed guarantee credit.
    # The Housing Benefit formulas still require someone over State Pension
    # age, so swapping this in reproduces the old behaviour exactly.
    value_type = bool
    entity = BenUnit
    definition_period = YEAR_PERIOD
    label = "computed guarantee credit (pre-fix passport test)"

    def formula(benunit, period, parameters):
        return benunit("guarantee_credit", period) > 0


VARIABLES = [
    "in_receipt_of_guarantee_credit",
    "pension_credit",
    "guarantee_credit",
    "is_pension_credit_eligible",
    "would_claim_pc",
    "housing_benefit",
    "housing_benefit_eligible",
    "housing_benefit_applicable_income",
    "housing_benefit_tariff_income",
    "housing_benefit_assessable_capital",
]
HB_OUTPUTS = VARIABLES[5:]


def calculate(units, old_formula=False, **kwargs):
    sim = Simulation(situation=situation(units, **kwargs))
    if old_formula:
        sim.tax_benefit_system.update_variable(in_receipt_of_guarantee_credit)
    values = {v: np.asarray(sim.calculate(v, YEAR)) for v in VARIABLES}
    values["any_over_sp_age"] = (
        np.asarray(sim.calculate("is_SP_age", YEAR, map_to="benunit")) > 0
    )
    # Person arrays follow the order the situation adds people in.
    claimant_or_partner = np.asarray(sim.calculate("is_claimant_or_partner", YEAR))
    sp_age = np.asarray(sim.calculate("is_SP_age", YEAR))
    starts = np.cumsum([0] + [len(unit["ages"]) for unit in units])
    values["claimants_and_partners_over_sp_age"] = np.array(
        [
            np.all(sp_age[a:b][claimant_or_partner[a:b].astype(bool)])
            for a, b in zip(starts[:-1], starts[1:])
        ]
    )
    return values


@PROPERTY_SETTINGS
@given(POPULATIONS)
def test_receipt_means_a_paid_guarantee_credit_and_passports(units):
    values = calculate(units)
    receipt = values["in_receipt_of_guarantee_credit"].astype(bool)
    paid = (values["pension_credit"] > 0) & (values["guarantee_credit"] > 0)
    assert np.array_equal(receipt, paid)
    assert not np.any(receipt & ~values["is_pension_credit_eligible"].astype(bool))
    assert not np.any(receipt & ~values["would_claim_pc"].astype(bool))
    assert np.all(values["claimants_and_partners_over_sp_age"][receipt])
    for variable in [
        "housing_benefit_applicable_income",
        "housing_benefit_tariff_income",
        "housing_benefit_assessable_capital",
    ]:
        assert np.all(values[variable][receipt] == 0), variable


@PROPERTY_SETTINGS
@given(POPULATIONS)
def test_matches_the_old_formula_when_pension_credit_is_claimed(units):
    new = calculate(units)
    old = calculate(units, old_formula=True)
    claimed = new["would_claim_pc"].astype(bool) & new[
        "is_pension_credit_eligible"
    ].astype(bool)
    for variable in HB_OUTPUTS:
        assert np.allclose(new[variable][claimed], old[variable][claimed], atol=0.01), (
            variable
        )
    old_passport = old["any_over_sp_age"] & old["in_receipt_of_guarantee_credit"]
    new_passport = new["any_over_sp_age"] & new["in_receipt_of_guarantee_credit"]
    # Intended difference: a computed guarantee credit that is not paid.
    computed_not_paid = (
        new["any_over_sp_age"]
        & (new["guarantee_credit"] > 0)
        & ~(new["pension_credit"] > 0)
    )
    assert np.array_equal(old_passport & ~new_passport, computed_not_paid)
    assert not np.any(new_passport & ~old_passport)
    assert not np.any(computed_not_paid & claimed)


@PROPERTY_SETTINGS
@given(POPULATIONS)
def test_not_claiming_pension_credit_never_raises_housing_benefit(units):
    claiming = calculate(units, would_claim_pc=True)
    not_claiming = calculate(units, would_claim_pc=False)
    assert not np.any(not_claiming["in_receipt_of_guarantee_credit"])
    assert np.all(not_claiming["housing_benefit"] <= claiming["housing_benefit"] + 0.01)


def test_pension_credit_freeze_keeps_the_baseline_receipt():
    # A pensioner with capital over £16,000 receives a guarantee credit of
    # 12,376 - (10,000 + 1,040) = 1,336 in the baseline. A reform setting the
    # single minimum guarantee to zero ends it; with Pension Credit frozen the
    # baseline award, guarantee credit included, is still paid.
    household = {
        "people": {
            "person": {
                "age": {YEAR: 70},
                "state_pension_reported": {YEAR: 10_000},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {
            "household": {
                "members": ["person"],
                "rent": {YEAR: 6_240},
                "tenure_type": {YEAR: "RENT_FROM_COUNCIL"},
                "savings": {YEAR: 20_000},
            }
        },
    }
    no_minimum_guarantee = {
        "gov.dwp.pension_credit.guarantee_credit.minimum_guarantee.SINGLE": 0
    }
    frozen = Simulation(
        situation=household,
        reform={**no_minimum_guarantee, "gov.contrib.freeze_pension_credit": True},
    )
    assert frozen.calculate("guarantee_credit", YEAR)[0] == 0
    assert abs(frozen.calculate("pension_credit", YEAR)[0] - 1_336) < 0.01
    assert frozen.calculate("in_receipt_of_guarantee_credit", YEAR)[0]
    assert frozen.calculate("housing_benefit_assessable_capital", YEAR)[0] == 0
    assert abs(frozen.calculate("housing_benefit", YEAR)[0] - 6_240) < 0.01

    unfrozen = Simulation(situation=household, reform=no_minimum_guarantee)
    assert unfrozen.calculate("pension_credit", YEAR)[0] == 0
    assert not unfrozen.calculate("in_receipt_of_guarantee_credit", YEAR)[0]
    assert unfrozen.calculate("housing_benefit_assessable_capital", YEAR)[0] == 20_000
    assert unfrozen.calculate("housing_benefit", YEAR)[0] == 0
