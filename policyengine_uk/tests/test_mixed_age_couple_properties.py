"""Mixed-age couples: State Pension Credit Act 2002 s.4(1A) and SI 2019/37.

From 15 May 2019 (SI 2019/37 art. 3) a member of a couple whose partner has
not reached the qualifying age for State Pension Credit is not entitled to
it, and the couple claims Universal Credit instead. Couples entitled to
Pension Credit or pension-age Housing Benefit on 14 May 2019 keep them while
they stay entitled (art. 4). Before that date a mixed-age couple could claim
Pension Credit and pension-age Housing Benefit.

Invariants, for every drawn household:

P1  pension_credit > 0 implies universal_credit == 0.
P2  housing_benefit > 0 implies universal_credit == 0.
P3  meets_pension_credit_age_conditions implies not is_uc_eligible (UC
    (Transitional Provisions) Regs 2014 reg 5(1)(d): one route per family).
P4  For a benefit unit that is not a mixed-age couple, the saving input
    changes nothing.
P5  Differential against the formulas before this change: units that are
    not mixed-age couples, and mixed-age couples without the saving from
    model year 2020, get the same Pension Credit, Housing Benefit, Universal
    Credit and household net income. The reference formulas read
    would_claim_uc alone, so no family here claims Universal Credit when a
    legacy award closes or is abolished. In model year 2026 both runs pay a
    working-age continuing award, an unsaved mixed-age couple's included,
    for the share of the year before the abolition of working-age Housing
    Benefit (housing_benefit_payable_share), so P5 compares those part-year
    awards.
P6  From model year 2020, the saving never lowers Pension Credit or Housing
    Benefit and leaves Universal Credit at 0.
P7  In model years 2018 and 2019 every mixed-age couple not reported on
    Universal Credit meets the Pension Credit age conditions, whatever the
    saving input; one reported on UC meets them only with the saving.
P8  The default saving is never set where the older member was born after
    5 February 1954 (so had not reached the qualifying age by 14 May 2019),
    or where the couple reports Universal Credit.
P9  From model year 2026 the abolition of working-age Housing Benefit (SI
    2025/1148 art. 7) reaches a mixed-age couple's award without the saving
    (payable share below 1) and not one with it (share 1): art. 7(4)(a)
    saves the couple only through reg 6A(5), which needs the saving.
    test_the_abolition_ends_only_an_unsaved_mixed_age_couples_award checks
    one couple's awards with and without a Universal Credit claim then.
"""

import json

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.model_api import *

OUTPUTS = ["pension_credit", "housing_benefit", "universal_credit"]
SHAPES = [
    "single_pension",
    "couple_pension",
    "mixed",
    "single_working",
    "couple_working",
    # An 18 year old dependant in upper secondary education is a qualifying
    # young person for Pension Credit, not a partner.
    "single_pension_with_dependant",
    "couple_pension_with_dependant",
    "mixed_with_dependant",
]
MIXED_AGE_COUPLE_SHAPES = {"mixed", "mixed_with_dependant"}
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
NORTH_WEST_BRMAS = [
    "CENTRAL_GREATER_MANCHESTER",
    "GREATER_LIVERPOOL",
    "EAST_CHESHIRE",
    "WEST_CUMBRIA",
]


# The three eligibility formulas as they were before the mixed-age couple
# rules, kept verbatim as the reference for the differential invariant P5.
# They read the claimant and partner (is_claimant_or_partner), so an 18 or 19
# year old dependant does not put a pensioner on the Universal Credit route.
class is_pension_credit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for Pension Credit (before the mixed-age couple rules)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        claimant_or_partner = benunit.members("is_claimant_or_partner", period)
        claimant_count = benunit.sum(claimant_or_partner)
        all_claimants_are_sp_age = (
            benunit.sum(claimant_or_partner & benunit.members("is_SP_age", period))
            == claimant_count
        )
        is_gc_eligible = benunit("is_guarantee_credit_eligible", period)
        is_sc_eligible = benunit("is_savings_credit_eligible", period)
        return (
            (claimant_count > 0)
            & all_claimants_are_sp_age
            & (is_gc_eligible | is_sc_eligible)
        )


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for Housing Benefit (before the mixed-age couple rules)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        person = benunit.members
        sp_age = person("is_SP_age", period)
        claimant_or_partner = person("is_claimant_or_partner", period)
        count = benunit.sum(claimant_or_partner)
        pension_age = (count > 0) & (benunit.sum(claimant_or_partner & sp_age) == count)
        already_claiming = add(benunit, period, ["housing_benefit_reported"]) > 0
        claiming_uc = benunit("would_claim_uc", period)
        continuing_award = already_claiming & ~claiming_uc
        social = benunit.any(person("in_social_housing", period))
        lha_eligible = benunit("LHA_eligible", period)
        any_over_SP_age = benunit.any(sp_age)
        capital = benunit("housing_benefit_assessable_capital", period)
        hb_capital = parameters(period).gov.dwp.housing_benefit.means_test.capital
        limit = where(
            any_over_SP_age,
            hb_capital.pension_age.limit,
            hb_capital.working_age.limit,
        )
        return (
            (pension_age | continuing_award)
            & (social | lha_eligible)
            & (capital <= limit)
        )


class is_uc_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligible for Universal Credit (before the mixed-age couple rules)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        capital = benunit("uc_assessable_capital", period)
        limit = parameters(period).gov.dwp.universal_credit.means_test.capital.limit
        claimant = benunit.members("is_uc_claimant", period)
        meets_minimum_age = benunit.members("meets_uc_minimum_age_condition", period)
        pension_age = benunit.members("is_SP_age", period)
        has_qualifying_claimant = benunit.any(
            claimant & meets_minimum_age & ~pension_age
        )
        return has_qualifying_claimant & (capital <= limit)


class before_mixed_age_couple_rules(Reform):
    def apply(self):
        self.update_variable(is_pension_credit_eligible)
        self.update_variable(housing_benefit_eligible)
        self.update_variable(is_uc_eligible)


@st.composite
def cases(draw):
    year = draw(st.sampled_from([2018, 2019, 2020, 2025, 2026]))
    shape = draw(st.sampled_from(SHAPES))
    pension_age = st.integers(67, 90)
    working_age = st.integers(25, 59)
    older_is_pension_age = "pension" in shape or shape.startswith("mixed")
    people = {
        "older": {"age": draw(pension_age if older_is_pension_age else working_age)}
    }
    if shape.startswith("couple") or shape.startswith("mixed"):
        people["younger"] = {
            "age": draw(
                pension_age if shape.startswith("couple_pension") else working_age
            )
        }
    if shape.endswith("with_dependant"):
        people["dependant"] = {"age": 18, "current_education": "UPPER_SECONDARY"}
        people["older"]["is_parent"] = True
    for name, person in people.items():
        # The older and younger members are the couple whatever their age gap,
        # so the roles are supplied rather than left to the age presumption.
        person["is_claimant_or_partner"] = name != "dependant"
        if name == "dependant":
            continue
        if person["age"] >= 67:
            person["state_pension"] = draw(st.integers(0, 15_000))
        else:
            person["employment_income"] = draw(
                st.sampled_from([0, 0, 5_000, 15_000, 30_000])
            )
    older = people["older"]
    older["pension_credit_reported"] = draw(st.sampled_from([0, 0, 1_000]))
    older["housing_benefit_reported"] = draw(st.sampled_from([0, 0, 4_000]))
    older["universal_credit_reported"] = draw(st.sampled_from([0, 0, 0, 2_000]))
    older["esa_income_reported"] = draw(st.sampled_from([0, 0, 0, 3_000]))
    tenure = draw(st.sampled_from(TENURES))
    return {
        "year": year,
        "shape": shape,
        "people": people,
        "benunit": {
            "would_claim_uc": draw(st.booleans()),
            "would_claim_pc": draw(st.booleans()),
            # The reference formulas read would_claim_uc alone, so no family
            # here claims when the abolition of income-related ESA or of
            # working-age Housing Benefit reaches its award in 2026-27.
            "would_claim_uc_at_legacy_closure": False,
        },
        "household": {
            "tenure_type": tenure,
            "rent": 0 if tenure == "OWNED_OUTRIGHT" else draw(st.integers(0, 12_000)),
            "savings": draw(st.sampled_from([0, 5_000, 20_000])),
            "region": "NORTH_WEST",
            # The LHA varies with the BRMA's published rates.
            "brma": draw(st.sampled_from(NORTH_WEST_BRMAS)),
            "council_tax": 1_500,
        },
    }


def situation(case):
    year = case["year"]

    def at_year(values):
        return {name: {year: value} for name, value in values.items()}

    members = list(case["people"])
    return {
        "people": {name: at_year(p) for name, p in case["people"].items()},
        "benunits": {"b": {"members": members, **at_year(case["benunit"])}},
        "households": {"h": {"members": members, **at_year(case["household"])}},
    }


def run(case, before=False, saving=None):
    simulation = Simulation(situation=situation(case))
    year = case["year"]
    if before:
        simulation.apply_reform(before_mixed_age_couple_rules)
    elif saving is not None:
        simulation.set_input(
            "has_mixed_age_couple_pension_credit_saving", year, [saving]
        )

    def get(variable):
        return simulation.calculate(variable, year)[0]

    result = {variable: float(get(variable)) for variable in OUTPUTS}
    result["net"] = float(get("household_net_income"))
    if not before:
        result["age_conditions"] = bool(get("meets_pension_credit_age_conditions"))
        result["uc_eligible"] = bool(get("is_uc_eligible"))
        result["mixed"] = bool(get("is_mixed_age_couple"))
        result["saving"] = bool(get("has_mixed_age_couple_pension_credit_saving"))
        result["payable_share"] = float(get("housing_benefit_payable_share"))
    return result


def close(a, b):
    return abs(a - b) < 0.01


@settings(
    max_examples=40,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(cases())
def test_mixed_age_couple_invariants(case):
    before = run(case, before=True)
    on = run(case, saving=True)
    off = run(case, saving=False)
    default = run(case)
    context = json.dumps(case)
    for result in (on, off, default):
        assert not (result["pension_credit"] > 0 and result["universal_credit"] > 0)
        assert not (result["housing_benefit"] > 0 and result["universal_credit"] > 0)
        assert not (result["age_conditions"] and result["uc_eligible"]), context
    mixed = on["mixed"]
    assert mixed == (case["shape"] in MIXED_AGE_COUPLE_SHAPES), context
    if not mixed:
        for variable in OUTPUTS + ["net"]:
            assert close(on[variable], off[variable]), (variable, context)  # P4
            assert close(on[variable], default[variable]), (variable, context)
            assert close(off[variable], before[variable]), (variable, context)  # P5
    elif case["year"] >= 2020:
        for variable in OUTPUTS + ["net"]:
            assert close(off[variable], before[variable]), (variable, context)  # P5
        assert on["pension_credit"] >= off["pension_credit"] - 0.01, context  # P6
        assert on["housing_benefit"] >= off["housing_benefit"] - 0.01, context
        assert on["universal_credit"] == 0, context
        if case["year"] >= 2026:  # P9
            assert off["payable_share"] < 1, context
            assert on["payable_share"] == 1, context
    else:
        # P7: before the exclusion only a couple reported on UC stays on it.
        on_uc = case["people"]["older"]["universal_credit_reported"] > 0
        assert on["age_conditions"], context
        assert off["age_conditions"] == (not on_uc), context
        assert default["age_conditions"] == (not on_uc), context
    older = case["people"]["older"]
    if default["saving"]:  # P8
        # A whole age places the birth on 6 April of year - age, which is on
        # or before 5 February 1954 only if year - age is 1953 or earlier.
        assert case["year"] - older["age"] <= 1953, context
        assert older["universal_credit_reported"] == 0, context


# The share of 2026-27 before 1 July 2026 (SI 2025/1148 art. 7(3)): 6 April
# to 30 June.
GREAT_BRITAIN_SHARE_2026 = 86 / 365


@pytest.mark.parametrize("saving", [False, True])
def test_the_abolition_ends_only_an_unsaved_mixed_age_couples_award(saving):
    # P9 for one couple (67 and 26) continuing a Housing Benefit award in
    # 2026-27. Without the saving the abolition reaches the award: a couple
    # that does not claim Universal Credit is paid for the part of the year
    # before 1 July 2026, and one that claims then gets no Housing Benefit
    # and the Universal Credit of any claim for the whole year, the model's
    # annual claim convention. With the saving (reg 6A(5), through art.
    # 7(4)(a)) the award continues for the whole year and prompts no claim.
    year = 2026

    def simulate(**benunit):
        case = {
            "year": year,
            "shape": "mixed",
            "people": {
                "older": {
                    "age": 67,
                    "is_claimant_or_partner": True,
                    "state_pension": 9_000,
                    "housing_benefit_reported": 4_000,
                },
                "younger": {"age": 26, "is_claimant_or_partner": True},
            },
            "benunit": {
                "would_claim_uc": False,
                "would_claim_pc": True,
                "would_claim_uc_at_legacy_closure": False,
                **benunit,
            },
            "household": {
                "tenure_type": "RENT_FROM_COUNCIL",
                "rent": 6_240,
                "savings": 0,
                "region": "NORTH_WEST",
                "brma": "CENTRAL_GREATER_MANCHESTER",
                "council_tax": 1_500,
            },
        }
        simulation = Simulation(situation=situation(case))
        simulation.set_input(
            "has_mixed_age_couple_pension_credit_saving", year, [saving]
        )
        return lambda variable: float(simulation.calculate(variable, year)[0])

    staying = simulate()
    claiming = simulate(would_claim_uc_at_legacy_closure=True)
    entitlement = staying("housing_benefit_entitlement")
    assert entitlement > 0
    if saving:
        for get in (staying, claiming):
            assert get("housing_benefit_payable_share") == 1
            assert not get("claims_uc_at_legacy_closure")
            assert close(get("housing_benefit_pre_benefit_cap"), entitlement)
            assert get("universal_credit") == 0
        return
    anyway = simulate(would_claim_uc=True)
    assert close(staying("housing_benefit_payable_share"), GREAT_BRITAIN_SHARE_2026)
    assert close(
        staying("housing_benefit_pre_benefit_cap"),
        entitlement * GREAT_BRITAIN_SHARE_2026,
    )
    assert staying("universal_credit") == 0
    assert claiming("claims_uc_at_legacy_closure")
    assert claiming("housing_benefit") == 0
    assert claiming("universal_credit") > 0
    assert close(claiming("universal_credit"), anyway("universal_credit"))
