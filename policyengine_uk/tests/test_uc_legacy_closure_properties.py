"""Property-based tests for Universal Credit claims when legacy benefits close.

Tax credits closed from 6 April 2025 and Income Support and income-based JSA
from 1 April 2026. DWP moved each family off its legacy benefits with a notice
covering all of them. A Universal Credit migration notice ends the awards on a
claim (SI 2014/1230 reg 8) or at its deadline (reg 46). A tax credit closure
notice sent families on Pension Credit, and families on Child Tax Credit but
not Working Tax Credit that meet the Pension Credit age conditions, to Pension
Credit instead (SI 2019/167 art. 3A). Pension-age families on Working Tax
Credit can claim Universal Credit (reg 60A), and a protected mixed-age couple
claims it jointly. Datasets say which families claim through
would_claim_uc_at_legacy_closure.

Invariants, for any generated population of families in 2024 to 2027:

1. Closure: legacy_benefits_closed holds exactly for a family that reports
   tax credits from 2025 and is not sent to Pension Credit, or reports Income
   Support or income-based JSA from 2026, is not on Pension Credit and is not
   wholly pension age.
2. Claim: claims_universal_credit is would_claim_uc, or the closure with the
   closure claim flag; Universal Credit is paid only to claiming families.
3. Migration ends every legacy award: a family moved off legacy benefits gets
   no tax credits, Income Support, income-related ESA or income-based JSA.
   It gets no Housing Benefit unless it is a wholly pension-age family that
   does not claim Universal Credit and so keeps the pension-age route.
   A family that leaves that route gets no Pension Credit either.
4. Exclusive: no family gets Universal Credit with Pension Credit or with
   Housing Benefit.
5. Metamorphic, the flag is inert unless it decides a claim: negating
   would_claim_uc_at_legacy_closure changes no benefit for a family not
   moved off legacy benefits, or for a working-age one that would claim
   Universal Credit anyway. In particular nothing changes in 2024, before
   any closure.
6. Differential: a working-age family claiming at the closure gets the
   benefits it would get if would_claim_uc were true.
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
    "mixed_age": [("claimant", PENSION_AGE), ("partner", WORKING_AGE)],
    "mixed_age_parents": [
        ("claimant", PENSION_AGE),
        ("partner", WORKING_AGE),
        ("child", st.integers(0, 15)),
    ],
}
LEGACY = (
    "child_tax_credit_reported",
    "working_tax_credit_reported",
    "housing_benefit_reported",
    "esa_income_reported",
    "income_support_reported",
    "jsa_income_reported",
    "pension_credit_reported",
)
TENURES = ["RENT_FROM_COUNCIL", "RENT_PRIVATELY", "OWNED_OUTRIGHT"]
BENEFITS = [
    "universal_credit",
    "housing_benefit",
    "pension_credit",
    "tax_credits",
    "income_support",
    "esa_income",
    "jsa_income",
]
OUTPUTS = BENEFITS + [
    "legacy_benefits_closed",
    "claims_universal_credit",
    "left_pension_route_at_legacy_closure",
    "meets_pension_credit_age_conditions",
    "is_mixed_age_couple",
]
award = st.sampled_from([0.0, 0.0, 2_000.0, 6_000.0])


@st.composite
def families(draw):
    shape = draw(st.sampled_from(sorted(SHAPES)))
    reported = {name: draw(award) for name in LEGACY}
    if not shape.startswith(("pensioner", "mixed_age")):
        reported["pension_credit_reported"] = 0.0
    return dict(
        shape=shape,
        members=[(role, draw(age)) for role, age in SHAPES[shape]],
        reported=reported,
        saving=draw(st.booleans()),
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
            "has_mixed_age_couple_pension_credit_saving": every_year(unit["saving"]),
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
    return {
        year: {v: np.asarray(sim.calculate(v, year)) for v in OUTPUTS} for year in YEARS
    }


def expected_closure(unit, year, pension_age_route, mixed_age):
    r = {name: amount > 0 for name, amount in unit["reported"].items()}
    wholly_pension_age = pension_age_route and not mixed_age
    tax_credits = r["child_tax_credit_reported"] or r["working_tax_credit_reported"]
    to_pension_credit = r["pension_credit_reported"] or (
        pension_age_route and not r["working_tax_credit_reported"]
    )
    is_or_jsa = r["income_support_reported"] or r["jsa_income_reported"]
    return (tax_credits and year >= 2025 and not to_pension_credit) or (
        is_or_jsa
        and year >= 2026
        and not r["pension_credit_reported"]
        and not wholly_pension_age
    )


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=25))
def test_closure_claims_and_the_end_of_legacy_awards(units):
    values = calculate(units)
    for year in YEARS:
        v = values[year]
        for i, unit in enumerate(units):
            pension_age_route = bool(v["meets_pension_credit_age_conditions"][i])
            mixed_age = bool(v["is_mixed_age_couple"][i])
            closed = expected_closure(unit, year, pension_age_route, mixed_age)
            assert bool(v["legacy_benefits_closed"][i]) == closed, (year, unit)
            claims_at_closure = closed and unit["claims_at_closure"]
            claims = unit["would_claim_uc"] or claims_at_closure
            assert bool(v["claims_universal_credit"][i]) == claims, (year, unit)
            if not claims:
                assert v["universal_credit"][i] == 0, (year, unit)
            assert not (v["universal_credit"][i] > 0 and v["pension_credit"][i] > 0)
            assert not (v["universal_credit"][i] > 0 and v["housing_benefit"][i] > 0)
            if not closed:
                continue
            for benefit in [
                "tax_credits",
                "income_support",
                "esa_income",
                "jsa_income",
            ]:
                assert v[benefit][i] == 0, (year, benefit, unit)
            left = pension_age_route and (claims_at_closure or mixed_age)
            assert bool(v["left_pension_route_at_legacy_closure"][i]) == left
            if left or not pension_age_route:
                assert v["housing_benefit"][i] == 0, (year, unit)
            if left:
                assert v["pension_credit"][i] == 0, (year, unit)


@PROPERTY_SETTINGS
@given(st.lists(families(), min_size=1, max_size=25))
def test_the_closure_flag_only_decides_closure_claims(units):
    drawn = calculate(units)
    negated = calculate(units, negate_flag=True)
    for year in YEARS:
        for i, unit in enumerate(units):
            # On the pension-age route would_claim_uc gives no Universal
            # Credit, so there the flag alone decides the closure claim.
            decides = bool(drawn[year]["legacy_benefits_closed"][i]) and (
                not unit["would_claim_uc"]
                or bool(drawn[year]["meets_pension_credit_age_conditions"][i])
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
        v = at_closure[year]
        for i, unit in enumerate(units):
            # On the pension-age route only a closure claim reaches Universal
            # Credit, so the two claims differ by design there.
            if (
                v["legacy_benefits_closed"][i]
                and not (v["meets_pension_credit_age_conditions"][i])
            ):
                for benefit in BENEFITS:
                    assert abs(v[benefit][i] - anyway[year][benefit][i]) < 0.01, (
                        year,
                        benefit,
                        unit,
                    )


@st.composite
def paid_legacy_families(draw):
    """Working-age families on tax credits and one other legacy award they
    are paid in 2024: no earnings or savings, and for Income Support a lone
    parent with a child under 5."""
    other = draw(
        st.sampled_from(
            ["income_support_reported", "esa_income_reported", "jsa_income_reported"]
        )
    )
    members = [("claimant", draw(st.integers(18, 60)))]
    members.append(("child", draw(st.integers(0, 4))))
    reported = {name: 0.0 for name in LEGACY}
    reported["child_tax_credit_reported"] = draw(st.sampled_from([2_000.0, 6_000.0]))
    reported[other] = draw(st.sampled_from([2_000.0, 6_000.0]))
    reported["housing_benefit_reported"] = draw(st.sampled_from([0.0, 3_000.0]))
    return dict(
        shape="lone_parent",
        members=members,
        reported=reported,
        saving=False,
        tenure="RENT_FROM_COUNCIL",
        rent=draw(st.floats(1_000, 8_000)),
        earnings=0.0,
        savings=0.0,
        would_claim_uc=False,
        claims_at_closure=draw(st.booleans()),
        other=other,
    )


@PROPERTY_SETTINGS
@given(st.lists(paid_legacy_families(), min_size=1, max_size=25))
def test_the_tax_credit_closure_ends_awards_paid_the_year_before(units):
    values = calculate(units)
    benefit = {
        "income_support_reported": "income_support",
        "esa_income_reported": "esa_income",
        "jsa_income_reported": "jsa_income",
    }
    for i, unit in enumerate(units):
        other = benefit[unit["other"]]
        # The generator only makes families paid the award before 2025.
        assert values[2024][other][i] > 0, unit
        assert values[2025]["legacy_benefits_closed"][i], unit
        assert values[2025][other][i] == 0, unit
        assert values[2025]["housing_benefit"][i] == 0, unit
