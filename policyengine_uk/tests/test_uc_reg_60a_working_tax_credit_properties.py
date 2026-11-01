"""Whose Working Tax Credit opens the reg 60A Universal Credit route.

SI 2014/1230 reg 60A(1) waives the upper age condition in WRA 2012
s.4(1)(b) for a qualifying claim by a single claimant, or joint claimants
both, who have reached the qualifying age for State Pension Credit and are
entitled to an award of Working Tax Credit. Members of a couple claim a tax
credit jointly (Tax Credits Act 2002 s.3(3)(a)); anyone else claims as a
single person (s.3(3)(b)). is_uc_eligible therefore reads the Working Tax
Credit reports of the claimant and partner (is_claimant_or_partner) only.

Invariants, for every drawn benefit unit:

P1  On a closure claim (claims_uc_at_legacy_closure), a Working Tax Credit
    report by a member who is neither claimant nor partner never changes
    is_uc_eligible.
P2  On a closure claim, with capital within the limit and a claimant or
    partner aged 18 or over, a positive report by the claimant or partner
    makes the family eligible.
P3  Without a closure claim, is_uc_eligible equals the formula that sums
    every member's report, whoever reports Working Tax Credit.
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from policyengine_core.reforms import Reform

from policyengine_uk import Simulation
from policyengine_uk.model_api import *

MODEL_YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Half the draws are unambiguously over the State Pension Credit
# qualifying age, where only the reg 60A route can open.
ADULT_AGE = st.one_of(st.integers(67, 100), st.integers(18, 100))
OTHER_AGE = st.integers(0, 60)
REPORT = st.sampled_from([0, 1, 500, 2_000, 6_000])
POSITIVE_REPORT = st.sampled_from([1, 500, 2_000, 6_000])
# Mostly no report, so other members' reports are often the only ones.
MOSTLY_NO_REPORT = st.sampled_from([0, 0, 0, 2_000])
# The 2026 capital limit is £16,000; draws straddle it.
CAPITAL = st.sampled_from([0, 6_000, 15_999, 16_001, 40_000])


class is_uc_eligible(Variable):
    """The formula that sums every benefit-unit member's Working Tax Credit
    report, the reference for P3."""

    value_type = bool
    entity = BenUnit
    label = "Eligible for Universal Credit (any member's Working Tax Credit)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        capital = benunit("uc_assessable_capital", period)
        limit = parameters(period).gov.dwp.universal_credit.means_test.capital.limit
        claimant = benunit.members("is_uc_single_or_joint_claimant", period)
        meets_minimum_age = benunit.members("meets_uc_minimum_age_condition", period)
        pension_age = benunit.members(
            "has_attained_state_pension_credit_qualifying_age", period
        )
        has_qualifying_claimant = benunit.any(
            claimant & meets_minimum_age & ~pension_age
        )
        pension_credit_route = benunit("meets_pension_credit_age_conditions", period)
        closure_claim = benunit("claims_uc_at_legacy_closure", period)
        on_working_tax_credit = (
            add(benunit, period, ["working_tax_credit_reported"]) > 0
        )
        reg_60a = on_working_tax_credit & benunit.any(claimant & meets_minimum_age)
        route = (has_qualifying_claimant & ~pension_credit_route) | (
            closure_claim & (has_qualifying_claimant | reg_60a)
        )
        return route & (capital <= limit)


class any_member_working_tax_credit(Reform):
    def apply(self):
        self.update_variable(is_uc_eligible)


@st.composite
def families(
    draw,
    couple_report=REPORT,
    couple_reports_wtc=False,
    other_report=REPORT,
    min_others=0,
):
    """A claimant, an optional partner and other members, each with
    is_claimant_or_partner set from their role. With couple_reports_wtc, the
    claimant or the partner reports a positive Working Tax Credit."""
    couple = ["claimant"] + (["partner"] if draw(st.booleans()) else [])
    people = {
        name: {
            "age": draw(ADULT_AGE),
            "is_claimant_or_partner": True,
            "working_tax_credit_reported": draw(couple_report),
        }
        for name in couple
    }
    if couple_reports_wtc:
        reporter = draw(st.sampled_from(couple))
        people[reporter]["working_tax_credit_reported"] = draw(POSITIVE_REPORT)
    for index in range(draw(st.integers(min_others, 2))):
        people[f"other_{index}"] = {
            "age": draw(OTHER_AGE),
            "is_claimant_or_partner": False,
            "working_tax_credit_reported": draw(other_report),
        }
    return {"people": people, "capital": draw(CAPITAL)}


def eligible(family, closure_claim, others_report=True, reform=None):
    people = {}
    for name, person in family["people"].items():
        values = dict(person)
        if not others_report and not values["is_claimant_or_partner"]:
            values["working_tax_credit_reported"] = 0
        people[name] = {key: {MODEL_YEAR: value} for key, value in values.items()}
    members = list(people)
    simulation = Simulation(
        situation={
            "people": people,
            "benunits": {
                "b": {
                    "members": members,
                    "claims_uc_at_legacy_closure": {MODEL_YEAR: closure_claim},
                    "uc_reported_capital": {MODEL_YEAR: family["capital"]},
                }
            },
            "households": {
                "h": {
                    "members": members,
                    "region": {MODEL_YEAR: "NORTH_EAST"},
                    "tenure_type": {MODEL_YEAR: "OWNED_OUTRIGHT"},
                }
            },
        }
    )
    if reform is not None:
        simulation.apply_reform(reform)
    return bool(simulation.calculate("is_uc_eligible", MODEL_YEAR)[0])


@PROPERTY_SETTINGS
@given(
    families(couple_report=MOSTLY_NO_REPORT, other_report=POSITIVE_REPORT, min_others=1)
)
def test_other_members_working_tax_credit_never_changes_closure_eligibility(family):
    assert eligible(family, closure_claim=True) == eligible(
        family, closure_claim=True, others_report=False
    )


@PROPERTY_SETTINGS
@given(families(couple_reports_wtc=True))
def test_claimant_or_partner_working_tax_credit_opens_closure_route(family):
    family = {**family, "capital": min(family["capital"], 15_999)}
    assert eligible(family, closure_claim=True)


@PROPERTY_SETTINGS
@given(families(couple_report=MOSTLY_NO_REPORT, other_report=POSITIVE_REPORT))
def test_no_closure_claim_matches_any_member_reading(family):
    assert eligible(family, closure_claim=False) == eligible(
        family, closure_claim=False, reform=any_member_working_tax_credit
    )


def test_other_adults_report_opens_route_under_any_member_reading():
    """The reference formula differs from the model on a closure claim, so
    P3's agreement without one is not vacuous."""
    family = {
        "people": {
            "claimant": {
                "age": 70,
                "is_claimant_or_partner": True,
                "working_tax_credit_reported": 0,
            },
            "other_0": {
                "age": 40,
                "is_claimant_or_partner": False,
                "working_tax_credit_reported": 1_000,
            },
        },
        "capital": 0,
    }
    assert not eligible(family, closure_claim=True)
    assert eligible(family, closure_claim=True, reform=any_member_working_tax_credit)
