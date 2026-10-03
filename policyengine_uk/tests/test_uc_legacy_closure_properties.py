"""Property-based tests for Universal Credit claims when legacy benefits close.

Tax credits closed from 6 April 2025 and Income Support and income-based JSA
from 1 April 2026. DWP moved each working-age family off its legacy benefits
with a migration notice covering all of them: the awards end on a Universal
Credit claim (SI 2014/1230 reg 8) or at the notice's deadline if the family
does not claim (reg 46). Datasets say which families claim through
would_claim_uc_at_legacy_closure.

Invariants, for any generated population of families in 2024 to 2027:

1. Closure: legacy_benefits_closed holds exactly for a working-age family
   (not on the pension-age route) that reports tax credits from 2025, or
   Income Support or income-based JSA from 2026.
2. Claim: claims_universal_credit is would_claim_uc, or the closure with the
   closure claim flag; Universal Credit is paid only to claiming families.
3. Migration ends every legacy award: a family whose legacy benefits have
   closed gets no Housing Benefit, tax credits, Income Support,
   income-related ESA or income-based JSA.
4. Metamorphic, the flag is inert unless it decides a claim: negating
   would_claim_uc_at_legacy_closure changes no benefit for a family whose
   legacy benefits have not closed or that would claim Universal Credit
   anyway. In particular nothing changes in 2024, before any closure.
5. Differential: a family claiming at the closure gets the Universal Credit
   it would get if would_claim_uc were true.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEARS = (2024, 2025, 2026, 2027)
PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# 67 and over is pension age in every year here; 60 and under working age.
PENSION_AGE = st.integers(67, 90)
WORKING_AGE = st.integers(18, 60)
SHAPES = {
    "single": [("claimant", WORKING_AGE)],
    "couple": [("claimant", WORKING_AGE), ("partner", WORKING_AGE)],
    "lone_parent": [("claimant", WORKING_AGE), ("child", st.integers(0, 15))],
    "couple_parents": [
        ("claimant", WORKING_AGE),
        ("partner", WORKING_AGE),
        ("child", st.integers(0, 15)),
    ],
    "pensioner": [("claimant", PENSION_AGE)],
    "pensioner_with_child": [("claimant", PENSION_AGE), ("child", st.integers(5, 15))],
}
LEGACY = (
    "child_tax_credit_reported",
    "working_tax_credit_reported",
    "housing_benefit_reported",
    "esa_income_reported",
    "income_support_reported",
    "jsa_income_reported",
)
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
BENEFITS = [
    "universal_credit",
    "housing_benefit",
    "tax_credits",
    "income_support",
    "esa_income",
    "jsa_income",
]
OUTPUTS = BENEFITS + ["legacy_benefits_closed", "claims_universal_credit"]
award = st.sampled_from([0.0, 0.0, 2_000.0, 6_000.0])


@st.composite
def families(draw):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    return dict(
        shape=shape,
        members=[(role, draw(age)) for role, age in SHAPES[shape]],
        reported={name: draw(award) for name in LEGACY},
        tenure=draw(st.sampled_from(TENURES)),
        rent=draw(st.floats(0, 12_000)),
        earnings=draw(st.sampled_from([0.0, 8_000.0, 25_000.0])),
        savings=draw(st.sampled_from([0.0, 5_000.0, 20_000.0])),
        would_claim_uc=draw(st.booleans()),
        claims_at_closure=draw(st.booleans()),
    )


def every_year(value):
    return {year: value for year in YEARS}


def situation(units, negate_flag=False, would_claim_uc=None):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, (role, age) in enumerate(unit["members"]):
            name = f"p{i}_{j}"
            # Set every input for every member, or it stops being an input
            # for the rest of the simulation.
            person = {
                "age": every_year(age),
                "is_claimant_or_partner": every_year(role != "child"),
                "employment_income": every_year(
                    unit["earnings"] if role == "claimant" else 0.0
                ),
            }
            for name_reported in LEGACY:
                amount = unit["reported"][name_reported] if role == "claimant" else 0
                person[name_reported] = every_year(amount)
            people[name] = person
            names.append(name)
        claims_anyway = (
            unit["would_claim_uc"] if would_claim_uc is None else would_claim_uc
        )
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": every_year(claims_anyway),
            "would_claim_uc_at_legacy_closure": every_year(
                unit["claims_at_closure"] ^ negate_flag
            ),
            "claims_all_entitled_benefits": every_year(False),
        }
        households[f"h{i}"] = {
            "members": names,
            "rent": every_year(unit["rent"]),
            "tenure_type": every_year(unit["tenure"]),
            "savings": every_year(unit["savings"]),
        }
    return {"people": people, "benunits": benunits, "households": households}


def calculate(units, **kwargs):
    sim = Simulation(situation=situation(units, **kwargs))
    values = {
        year: {v: np.asarray(sim.calculate(v, year)) for v in OUTPUTS} for year in YEARS
    }
    for year in YEARS:
        values[year]["pension_route"] = np.asarray(
            sim.calculate("meets_pension_credit_age_conditions", year)
        )
    return values


def expected_closure(unit, year, pension_route):
    reported = unit["reported"]
    tax_credits = (
        reported["child_tax_credit_reported"] + reported["working_tax_credit_reported"]
    )
    is_or_jsa = reported["income_support_reported"] + reported["jsa_income_reported"]
    closed = (tax_credits > 0 and year >= 2025) or (is_or_jsa > 0 and year >= 2026)
    return closed and not pension_route


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=25))
def test_closure_claims_and_the_end_of_legacy_awards(units):
    values = calculate(units)
    for year in YEARS:
        v = values[year]
        for i, unit in enumerate(units):
            closed = expected_closure(unit, year, bool(v["pension_route"][i]))
            assert bool(v["legacy_benefits_closed"][i]) == closed, (year, unit)
            claims = unit["would_claim_uc"] or (closed and unit["claims_at_closure"])
            assert bool(v["claims_universal_credit"][i]) == claims, (year, unit)
            if not claims:
                assert v["universal_credit"][i] == 0, (year, unit)
            if closed:
                for benefit in BENEFITS[1:]:
                    assert v[benefit][i] == 0, (year, benefit, unit)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=25))
def test_the_closure_flag_only_decides_closure_claims(units):
    drawn = calculate(units)
    negated = calculate(units, negate_flag=True)
    for year in YEARS:
        for i, unit in enumerate(units):
            decides = (
                bool(drawn[year]["legacy_benefits_closed"][i])
                and not unit["would_claim_uc"]
            )
            if year == 2024:
                assert not decides, unit
            if decides:
                continue
            for benefit in BENEFITS:
                assert drawn[year][benefit][i] == negated[year][benefit][i], (
                    year,
                    benefit,
                    unit,
                )


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=25))
def test_a_closure_claim_pays_the_universal_credit_of_any_claim(units):
    for unit in units:
        unit["claims_at_closure"] = True
    at_closure = calculate(units, would_claim_uc=False)
    anyway = calculate(units, would_claim_uc=True)
    for year in YEARS:
        closed = at_closure[year]["legacy_benefits_closed"]
        for i, unit in enumerate(units):
            if closed[i]:
                for benefit in BENEFITS:
                    assert (
                        abs(at_closure[year][benefit][i] - anyway[year][benefit][i])
                        < 0.01
                    ), (year, benefit, unit)
