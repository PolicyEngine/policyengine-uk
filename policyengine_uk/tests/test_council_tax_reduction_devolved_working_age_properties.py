"""Properties of the Scottish and Welsh working-age council tax reduction.

Invariants, for any working-age family in Scotland or Wales:

1. The award is between 0 and the council tax liability.
2. Wales, Universal Credit: the award does not depend on the rent. The UC
   housing costs element sits in both the applicable amount (the UC maximum
   amount, WSI 2013/3029 Sch 6 para 3) and the income (the award, para 9), so
   it cancels. Benefit-capped awards are excluded: the cap lowers the award
   but not the maximum amount.
3. Universal Credit, both countries: the award never rises with the
   claimant's earnings. In Wales excess income is the Secretary of State's
   income plus the award less the maximum amount, which rises by at least 45p
   for each £1 of net earnings. In Scotland only the child and childcare
   elements of the award count (SSI 2021/249 reg 57(1)(p)), so income rises
   by at least 45p for each £1 as well.
4. A claimant on income-related ESA and not on Universal Credit gets the
   whole liability (SSI 2021/249 reg 13(11); WSI 2013/3029 Sch 9 para 8),
   whatever their earnings.

Each example puts every family and its variants in one simulation, so the
formulas also run on arrays with several benefit units and households.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from policyengine_uk import Simulation

YEAR = 2026
REGIONS = ["SCOTLAND", "WALES"]


@st.composite
def families(draw):
    region = draw(st.sampled_from(REGIONS))
    couple = draw(st.booleans())
    children = draw(st.integers(0, 3))
    people = [
        {
            "age": draw(st.integers(18, 60)),
            "employment_income": draw(st.floats(0, 40_000)),
            "weekly_hours": draw(st.sampled_from([0, 10, 20, 35])),
            "council_tax_benefit_reported": 100,
        }
    ]
    if couple:
        people.append(
            {
                "age": draw(st.integers(18, 60)),
                "employment_income": draw(st.floats(0, 20_000)),
            }
        )
    for _ in range(children):
        people.append({"age": draw(st.integers(0, 15))})
    return {
        "region": region,
        "people": people,
        "would_claim_uc": draw(st.booleans()),
        "rent": draw(st.floats(0, 12_000)),
        "council_tax": draw(st.floats(500, 3_500)),
        "savings": draw(st.floats(0, 15_000)),
        "esa_income": 0,
    }


def situation(units):
    people, benunits, households = {}, {}, {}
    for i, unit in enumerate(units):
        names = []
        for j, inputs in enumerate(unit["people"]):
            name = f"p{i}_{j}"
            people[name] = {k: {YEAR: v} for k, v in inputs.items()}
            names.append(name)
        benunits[f"b{i}"] = {
            "members": names,
            "would_claim_uc": {YEAR: unit["would_claim_uc"]},
            "esa_income": {YEAR: unit["esa_income"]},
        }
        households[f"h{i}"] = {
            "members": names,
            "region": {YEAR: unit["region"]},
            "country": {YEAR: unit["region"]},
            "rent": {YEAR: unit["rent"]},
            "council_tax": {YEAR: unit["council_tax"]},
            "savings": {YEAR: unit["savings"]},
        }
    return {"people": people, "benunits": benunits, "households": households}


def with_earnings_raised(unit, amount):
    people = [dict(p) for p in unit["people"]]
    people[0]["employment_income"] = people[0]["employment_income"] + amount
    return {**unit, "people": people}


SETTINGS = settings(
    max_examples=20,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=5), st.floats(100, 5_000))
def test_devolved_working_age_award_properties(units, raise_by):
    n = len(units)
    variants = (
        units
        + [{**u, "rent": u["rent"] * 2 + 1_000} for u in units]
        + [with_earnings_raised(u, raise_by) for u in units]
    )
    sim = Simulation(situation=situation(variants))
    award = sim.calculate("simulated_council_tax_reduction_benunit", YEAR)
    working_age = sim.calculate("council_tax_reduction_devolved_working_age", YEAR)
    has_uc = sim.calculate(
        "council_tax_reduction_working_age_has_universal_credit", YEAR
    )
    capped = sim.calculate("benefit_cap_reduction", YEAR) > 0
    liability = sim.calculate(
        "council_tax_reduction_maximum_eligible_liability", YEAR, map_to="benunit"
    )
    for i in range(n):
        assert working_age[i], units[i]
        # 1. Bounds.
        assert -0.01 <= award[i] <= liability[i] + 0.01, units[i]
        # 2. Wales UC: the rent cancels.
        rent_i = n + i
        if (
            units[i]["region"] == "WALES"
            and has_uc[i]
            and has_uc[rent_i]
            and not capped[i]
            and not capped[rent_i]
        ):
            assert abs(award[i] - award[rent_i]) < 0.01, units[i]
        # 3. UC: more earnings never raise the award.
        earn_i = 2 * n + i
        if has_uc[i] and has_uc[earn_i] and not capped[i] and not capped[earn_i]:
            assert award[earn_i] <= award[i] + 0.01, units[i]


@SETTINGS
@given(st.lists(families(), min_size=1, max_size=5))
def test_income_related_esa_passports_to_the_full_liability(units):
    passported = [
        {**u, "would_claim_uc": False, "esa_income": 4_000, "savings": 0} for u in units
    ]
    sim = Simulation(situation=situation(passported))
    award = sim.calculate("simulated_council_tax_reduction_benunit", YEAR)
    liability = sim.calculate(
        "council_tax_reduction_maximum_eligible_liability", YEAR, map_to="benunit"
    )
    flag = sim.calculate("council_tax_reduction_working_age_passported", YEAR)
    assert flag.all()
    assert np.allclose(award, liability, atol=0.01)


def welsh_universal_credit_family(earnings, rent, statutory_maternity_pay=0):
    return {
        "region": "WALES",
        "people": [
            {
                "age": 30,
                "employment_income": earnings,
                "weekly_hours": 30,
                "council_tax_benefit_reported": 100,
            },
            {"age": 30, "statutory_maternity_pay": statutory_maternity_pay},
            {"age": 0},
        ],
        "would_claim_uc": True,
        "rent": rent,
        "council_tax": 1_800,
        "savings": 0,
        "esa_income": 0,
    }


def test_welsh_universal_credit_uses_the_universal_credit_income_figure():
    """Wales with Universal Credit (WSI 2013/3029 Sch 6 paras 3 and 9).

    The applicable amount is the UC maximum amount, and income is the
    Secretary of State's income figure for the award plus the award. Earnings
    are therefore whatever the UC model counts, statutory pay included or
    not, so CTR and UC can never disagree on them. Differential check against
    the UC variables, with and without statutory maternity pay.
    """
    units = [
        welsh_universal_credit_family(6_000, 6_000),
        welsh_universal_credit_family(6_000, 6_000, statutory_maternity_pay=5_000),
        welsh_universal_credit_family(8_000, 6_000),
    ]
    sim = Simulation(situation=situation(units))
    earnings = sim.calculate("council_tax_reduction_working_age_earned_income", YEAR)
    uc_earnings = sim.calculate("uc_individual_earned_income", YEAR, map_to="benunit")
    award = sim.calculate(
        "council_tax_reduction_working_age_universal_credit_award", YEAR
    )
    income = sim.calculate("council_tax_reduction_working_age_applicable_income", YEAR)
    applicable_amount = sim.calculate(
        "council_tax_reduction_working_age_applicable_amount", YEAR
    )
    assert sim.calculate(
        "council_tax_reduction_working_age_has_universal_credit", YEAR
    ).all()
    assert np.allclose(earnings, uc_earnings, atol=0.01)
    assert np.allclose(
        income,
        earnings + sim.calculate("uc_unearned_income", YEAR) + award,
        atol=0.01,
    )
    assert np.allclose(
        applicable_amount, sim.calculate("uc_maximum_amount", YEAR), atol=0.01
    )


def test_welsh_universal_credit_partial_award_does_not_depend_on_rent():
    """A targeted case for property 2, where the award is partial.

    Couple with a baby, £11,000 earnings (above the benefit cap's earnings
    exemption) and rent of £6,000 or £13,000. The housing element raises both
    the maximum amount and the award, so excess income, 0.45 x 11,000 + 0.55
    x 5,124 work allowance = 7,768.20, and the award, 1,800 - 0.2 x 7,768.20
    = 246.36, are the same at either rent.
    """
    units = [
        welsh_universal_credit_family(11_000, 6_000),
        welsh_universal_credit_family(11_000, 13_000),
    ]
    sim = Simulation(situation=situation(units))
    award = sim.calculate("simulated_council_tax_reduction_benunit", YEAR)
    assert sim.calculate("benefit_cap_reduction", YEAR).max() == 0
    assert np.allclose(award, 246.36, atol=0.01)


def test_welsh_fixed_amounts_start_with_the_2013_scheme():
    """Wales's fixed working-age amounts apply from 1 April 2013, when the
    Council Tax Reduction Schemes (Prescribed Requirements) (Wales)
    Regulations 2012 (W.S.I. 2012/3144) set them. A parameter read before its
    first date takes its earliest value, so check the first dates."""
    from policyengine_uk.system import system

    wales = system.parameters.gov.local_authorities.wales.council_tax_reduction
    working_age = wales.working_age
    first = {
        "earnings_disregard.single": 5,
        "earnings_disregard.couple": 10,
        "earnings_disregard.lone_parent": 25,
        "earnings_disregard.disability_or_carer": 20,
        "earnings_disregard.additional": 17.10,
        "tariff_income.threshold": 6_000,
        "tariff_income.step": 250,
        "tariff_income.amount": 1,
        "childcare.maximum_one_child": 175,
        "childcare.maximum_two_or_more_children": 300,
    }
    for name, value in first.items():
        parameter = working_age.get_child(name)
        earliest = parameter.values_list[-1]
        assert earliest.instant_str == "2013-04-01", name
        assert earliest.value == value, name
