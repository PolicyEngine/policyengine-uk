"""Property-based tests for the end of income-related ESA on a Universal
Credit claim (#1914).

A claim for Universal Credit brings the abolition of income-related ESA
(Welfare Reform Act 2012 s.33(1)(b)) into force for the claimant's old style
ESA award, whether or not Universal Credit is awarded (SI 2013/983 art. 4(1),
(2)(a), (3)(a) and (9); NI: SR 2017/190 art. 6). The claim is the claimant's
and partner's. A member who is neither, such as a non-dependent adult, claims
income-related ESA in their own right and is not part of it.

Invariants, for any generated population of working-age families in 2025
and 2027 (either side of income-related ESA's 1 July 2026 abolition date,
which the model does not yet apply) with no other legacy benefit, so none is
moved off legacy benefits:

1. Exclusive: a family that claims Universal Credit pays its claimant and
   partner no income-related ESA (claimant_or_partner_esa_income), and
   neither of them is on it (is_on_income_related_esa). So Universal Credit
   and the claimant's or partner's income-related ESA are never both paid.
   Without a claim the gate is inert: esa_income_report_closed is
   person_legacy_benefits_closed.
2. Differential: claiming Universal Credit gives the same income-related ESA
   outcomes (esa_income, claimant_or_partner_esa_income, esa_income_eligible
   and each member's is_on_income_related_esa) as not claiming with the
   claimant's and partner's reports removed. Another member's own award is
   what it would be if the couple had never reported one.

Intended: claiming Universal Credit can raise esa_income. While the claimant
or partner reports an award, the benefit unit's screen tests only them, and
another member's report is paid or not with their claim
(esa_income_eligible). Once the claim ends the couple's award, that member is
screened on their own claim alone, as invariant 2 says.
"""

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")

YEARS = (2025, 2027)
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
WORKING_AGE = st.integers(25, 60)
# "other" is an adult who is neither the claimant, the partner nor a young
# person they are responsible for, so they claim in their own right.
SHAPES = {
    "single": ["claimant"],
    "couple": ["claimant", "partner"],
    "lone_parent": ["claimant", "child"],
    "single_with_other": ["claimant", "other"],
    "couple_with_other": ["claimant", "partner", "other"],
}
REPORT = st.sampled_from([0.0, 2_000.0, 6_000.0])
BENUNIT_OUTPUTS = [
    "esa_income",
    "claimant_or_partner_esa_income",
    "esa_income_eligible",
    "claims_universal_credit",
    "universal_credit",
]
PERSON_OUTPUTS = [
    "is_on_income_related_esa",
    "is_claimant_or_partner",
    "esa_income_report_closed",
    "person_legacy_benefits_closed",
]


@st.composite
def families(draw):
    roles = SHAPES[draw(st.sampled_from(sorted(SHAPES)))]
    members = []
    for role in roles:
        members.append(
            dict(
                role=role,
                age=draw(st.integers(0, 15) if role == "child" else WORKING_AGE),
                esa_income_reported=0.0 if role == "child" else draw(REPORT),
                employment_income=(
                    0.0
                    if role == "child"
                    else draw(st.sampled_from([0.0, 0.0, 4_000.0, 20_000.0]))
                ),
                weekly_hours=0.0
                if role == "child"
                else draw(st.sampled_from([0, 10, 30])),
            )
        )
    return dict(
        members=members,
        # Around the £6,000 tariff threshold and £16,000 limit.
        savings=draw(st.sampled_from([0.0, 7_000.0, 20_000.0])),
        would_claim_uc=draw(st.booleans()),
    )


def every_year(value):
    return {year: value for year in YEARS}


def situation(units, would_claim_uc=None, drop_couple_reports=False):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, member in enumerate(unit["members"]):
            name = f"p{i}_{j}"
            couple = member["role"] in ("claimant", "partner")
            report = member["esa_income_reported"]
            if drop_couple_reports and couple:
                report = 0.0
            # Set every input for every member, or it stops being an input
            # for the rest of the simulation.
            people[name] = {
                "age": every_year(member["age"]),
                "is_claimant_or_partner": every_year(couple),
                "current_education": every_year("NOT_IN_EDUCATION"),
                "esa_income_reported": every_year(report),
                "employment_income": every_year(member["employment_income"]),
                "weekly_hours": every_year(member["weekly_hours"]),
            }
            names.append(name)
        claims = unit["would_claim_uc"] if would_claim_uc is None else would_claim_uc
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": every_year(claims),
            "claims_all_entitled_benefits": every_year(False),
        }
        households[f"h{i}"] = {
            "members": names,
            "savings": every_year(unit["savings"]),
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, **kwargs):
    sim = Simulation(situation=situation(units, **kwargs))
    return {
        year: {
            v: np.asarray(sim.calculate(v, year))
            for v in BENUNIT_OUTPUTS + PERSON_OUTPUTS
        }
        for year in YEARS
    }


def members_of(units):
    """Each person's benefit unit index, in simulation order."""
    return np.array([i for i, unit in enumerate(units) for _ in unit["members"]])


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=12))
def test_a_universal_credit_claim_ends_the_couples_income_related_esa(units):
    values = calculate(units)
    benunit = members_of(units)
    for year in YEARS:
        v = values[year]
        claims = v["claims_universal_credit"].astype(bool)
        # Nothing here moves a family off legacy benefits, so the claim is
        # would_claim_uc.
        assert list(claims) == [unit["would_claim_uc"] for unit in units]
        assert np.all(v["claimant_or_partner_esa_income"][claims] == 0), year
        assert not np.any(
            v["is_on_income_related_esa"].astype(bool)
            & v["is_claimant_or_partner"].astype(bool)
            & claims[benunit]
        ), year
        paid_uc = v["universal_credit"] > 0
        assert not np.any(paid_uc & (v["claimant_or_partner_esa_income"] > 0)), year
        not_claiming = ~claims[benunit]
        assert np.array_equal(
            v["esa_income_report_closed"][not_claiming],
            v["person_legacy_benefits_closed"][not_claiming],
        ), year


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=12))
def test_a_claim_is_the_couple_reporting_no_income_related_esa(units):
    claiming = calculate(units, would_claim_uc=True)
    without_couple_reports = calculate(
        units, would_claim_uc=False, drop_couple_reports=True
    )
    for year in YEARS:
        for name in [
            "esa_income",
            "claimant_or_partner_esa_income",
            "esa_income_eligible",
            "is_on_income_related_esa",
        ]:
            assert np.allclose(
                claiming[year][name].astype(float),
                without_couple_reports[year][name].astype(float),
                atol=0.01,
            ), (year, name)
