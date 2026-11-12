"""Whose Working Tax Credit opens the reg 60A Universal Credit route.

Under SI 2014/1230 reg 60A(1), the upper age condition in WRA 2012 s.4(1)(b)
does not apply to a qualifying claim by a single claimant, or joint
claimants both, who have reached the qualifying age for State Pension
Credit, hold an award of Working Tax Credit and hold no award of State
Pension Credit when the migration notice is issued. A couple both aged 16
or over and in the UK must claim a tax credit together (Tax Credits Act 2002
s.3(3)), and s.10(1) ties entitlement to "the person or persons by whom a
claim ... has been made". is_uc_eligible reads the Working Tax Credit
reports of the claimant and partner (is_claimant_or_partner) only.

Invariants, for every drawn benefit unit:

P1  On a closure claim (claims_uc_at_legacy_closure), a Working Tax Credit
    report by a member who is neither claimant nor partner never changes
    is_uc_eligible.
P2  On a closure claim, with capital within the limit and a claimant aged
    18 or over, a positive report by the claimant or partner makes the
    family eligible.
P3  Without a closure claim, zeroing every member's Working Tax Credit
    report never changes is_uc_eligible.
P4  On a closure claim, moving a Working Tax Credit report between claimant
    and partner never changes is_uc_eligible.
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

MODEL_YEAR = 2026
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Half the adult draws fall from 67 to 100, past the State Pension Credit
# qualifying age, where only the reg 60A route can open.
ADULT_AGE = st.one_of(st.integers(67, 100), st.integers(18, 100))
# These draws set no carer or limited capability for work input, so a
# partner aged 16 or 17 meets the minimum age condition
# (meets_uc_minimum_age_condition) only beside a member under 16. Without
# one, the partner can't be a joint claimant of Universal Credit (UC Regs
# 2013 reg 3(3)) but still holds the couple's tax credit award.
PARTNER_AGE = st.one_of(st.integers(67, 100), st.integers(16, 17), ADULT_AGE)
OTHER_AGE = st.integers(0, 60)
REPORT = st.sampled_from([0, 1, 500, 2_000, 6_000])
POSITIVE_REPORT = st.sampled_from([1, 500, 2_000, 6_000])
# Three draws in four report nothing, so another member often reports alone.
MOSTLY_NO_REPORT = st.sampled_from([0, 0, 0, 2_000])
# The draws straddle the £16,000 capital limit for 2026.
CAPITAL = st.sampled_from([0, 6_000, 15_999, 16_001, 40_000])
WITHIN_LIMIT = 15_999


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
    people = {
        "claimant": {
            "age": draw(ADULT_AGE),
            "is_claimant_or_partner": True,
            "working_tax_credit_reported": draw(couple_report),
        }
    }
    if draw(st.booleans()):
        people["partner"] = {
            "age": draw(PARTNER_AGE),
            "is_claimant_or_partner": True,
            "working_tax_credit_reported": draw(couple_report),
        }
    if couple_reports_wtc:
        reporter = draw(st.sampled_from(list(people)))
        people[reporter]["working_tax_credit_reported"] = draw(POSITIVE_REPORT)
    for index in range(draw(st.integers(min_others, 2))):
        people[f"other_{index}"] = {
            "age": draw(OTHER_AGE),
            "is_claimant_or_partner": False,
            "working_tax_credit_reported": draw(other_report),
        }
    return {"people": people, "capital": draw(CAPITAL)}


def eligible(family, closure_claim, zero_reports=None):
    """is_uc_eligible for the family. zero_reports is "others" to zero the
    reports of members who are neither claimant nor partner, or "all" to
    zero every member's report."""
    people = {}
    for name, person in family["people"].items():
        values = dict(person)
        if zero_reports == "all" or (
            zero_reports == "others" and not values["is_claimant_or_partner"]
        ):
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
    return bool(simulation.calculate("is_uc_eligible", MODEL_YEAR)[0])


@PROPERTY_SETTINGS
@given(
    families(couple_report=MOSTLY_NO_REPORT, other_report=POSITIVE_REPORT, min_others=1)
)
def test_other_members_working_tax_credit_never_changes_closure_eligibility(family):
    assert eligible(family, closure_claim=True) == eligible(
        family, closure_claim=True, zero_reports="others"
    )


@PROPERTY_SETTINGS
@given(families(couple_reports_wtc=True))
def test_claimant_or_partner_working_tax_credit_opens_closure_route(family):
    family = {**family, "capital": min(family["capital"], WITHIN_LIMIT)}
    assert eligible(family, closure_claim=True)


@PROPERTY_SETTINGS
@given(families(couple_reports_wtc=True, other_report=POSITIVE_REPORT))
def test_working_tax_credit_never_changes_eligibility_without_closure_claim(family):
    # Every draw has a report by the claimant or partner and capital within
    # the limit, so a reg 60A route that opened without a closure claim
    # would make a wholly pension-age family eligible.
    family = {**family, "capital": min(family["capital"], WITHIN_LIMIT)}
    assert eligible(family, closure_claim=False) == eligible(
        family, closure_claim=False, zero_reports="all"
    )


def test_working_tax_credit_changes_eligibility_on_closure_claim():
    """On a closure claim, zeroing a pension-age claimant's own report closes
    the route, so the zeroing that P3 applies without a closure claim can
    change is_uc_eligible."""
    family = {
        "people": {
            "claimant": {
                "age": 70,
                "is_claimant_or_partner": True,
                "working_tax_credit_reported": 1_000,
            },
        },
        "capital": 0,
    }
    assert eligible(family, closure_claim=True)
    assert not eligible(family, closure_claim=True, zero_reports="all")


@st.composite
def couples(draw):
    """A claimant and a partner, one of whom reports Working Tax Credit."""
    people = {
        "claimant": {
            "age": draw(ADULT_AGE),
            "is_claimant_or_partner": True,
            "working_tax_credit_reported": 0,
        },
        "partner": {
            "age": draw(PARTNER_AGE),
            "is_claimant_or_partner": True,
            "working_tax_credit_reported": 0,
        },
    }
    people[draw(st.sampled_from(["claimant", "partner"]))][
        "working_tax_credit_reported"
    ] = draw(POSITIVE_REPORT)
    for index in range(draw(st.integers(0, 1))):
        people[f"other_{index}"] = {
            "age": draw(OTHER_AGE),
            "is_claimant_or_partner": False,
            "working_tax_credit_reported": 0,
        }
    return {"people": people, "capital": WITHIN_LIMIT}


def swapped(family):
    people = {name: dict(person) for name, person in family["people"].items()}
    claimant, partner = people["claimant"], people["partner"]
    claimant["working_tax_credit_reported"], partner["working_tax_credit_reported"] = (
        partner["working_tax_credit_reported"],
        claimant["working_tax_credit_reported"],
    )
    return {**family, "people": people}


@PROPERTY_SETTINGS
@given(couples())
def test_moving_report_between_claimant_and_partner_never_changes_closure_eligibility(
    family,
):
    assert eligible(family, closure_claim=True) == eligible(
        swapped(family), closure_claim=True
    )
