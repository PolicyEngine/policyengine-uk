"""Property-based and exhaustive tests for the Housing Benefit and national
Council Tax Reduction non-dependant deductions.

Law:
- Housing Benefit: SI 2006/213 reg 74 (working age) and SI 2006/214 reg 55
  (pension age).
- Council Tax Reduction: SI 2012/2885 Sch 1 para 8 (England, pensioners);
  WSI 2013/3029 Sch 1 para 3 and Sch 6 para 5 (Wales); SSI 2012/319 reg 48 and
  SSI 2021/249 reg 90 (Scotland).

Invariants, for any generated population of households, each a claimant family
and a non-dependant family of one or two adults:

1. An exempt non-dependant's individual deduction is 0, for Housing Benefit and
   for Council Tax Reduction.
2. Bounds: an eligible non-dependant who is not exempt pays between the
   scale's lowest and highest weekly amounts. In English working-age
   households (local schemes) the national CTR deduction is 0.
3. A non-dependant not in remunerative work (under 16 hours or, for Housing
   Benefit, on IS, JSA(IB) or ESA(IR): HB reg 6(6)) pays the lowest amount,
   whatever their income.
4. If the claimant or partner is exempt, the claimant family's deductions
   are 0.
5. Aggregation: a family's deductions are the sum, over the other families in
   the household, of their claimant and partner's higher amount (both amounts
   for a Welsh working-age applicant's non-dependant couple with a Universal
   Credit award) plus each other member's, recomputed here from the
   individual amounts.
6. Monotonicity (metamorphic): raising any non-dependant's income never lowers
   an individual deduction or a family's deductions.
7. Exhaustive: in every year from 2015 (2019 for Housing Benefit) to 2030,
   including uprated years, an income at a band's lower edge gets that band's
   amount and the next lower representable income gets the band below's.
8. Differential: each CTR scale's parameter equals the enacted sums in
   tests/fixtures/council_tax_reduction_non_dependant_deductions.yaml.
9. Differential: each exemption flag equals a reading of the provisions
   straight from the generated inputs. Housing Benefit: a full-time student,
   a State Pension Credit recipient, or under 25 and on Income Support,
   income-based JSA or Universal Credit without earned income. CTR (any age):
   a full-time student, on IS, JSA(IB), ESA(IR) or SPC, or, in a national
   scheme, on Universal Credit without earned income. Benefit receipt counts
   only for the claimant or partner of the award; a self-employed loss counts
   as nil earnings (UC reg 57(2)).
"""

from pathlib import Path

import numpy as np
import pytest
import yaml
from hypothesis import HealthCheck, example, given, settings
from hypothesis import strategies as st

from policyengine_uk import CountryTaxBenefitSystem, Simulation

PROPERTY_SETTINGS = settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
# Local authorities without a modelled local scheme.
COUNTRIES = {
    "ENGLAND": "MAIDSTONE",
    "WALES": "CARDIFF",
    "SCOTLAND": "GLASGOW_CITY",
}
CTR_SCALES = {
    "ENGLAND": "england.council_tax_reduction.pensioners.non_dep_deduction",
    "WALES": "wales.council_tax_reduction.non_dep_deduction",
    "SCOTLAND": "scotland.council_tax_reduction.non_dep_deduction",
}
FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "council_tax_reduction_non_dependant_deductions.yaml"
)
WEEKS = 52
CLAIMANT_DISABILITY = [
    None,
    None,
    None,
    "is_blind",
    "attendance_allowance",
    "dla_sc",
    "pip_dl",
    "armed_forces_independence_payment",
]
BENEFITS = [
    "income_support",
    "jsa_income",
    "esa_income",
    "pension_credit",
    "universal_credit_pre_benefit_cap",
]
# Family benefits counted in gross income, held at zero so the oracle knows
# each family's gross income.
OTHER_FAMILY_BENEFITS = ["child_tax_credit", "working_tax_credit", "child_benefit"]
SYSTEM = CountryTaxBenefitSystem()


def for_years(situation, years):
    """Key every input by year: unkeyed inputs apply only to the default
    period."""
    for group in situation.values():
        for entity in group.values():
            for key, value in entity.items():
                if key != "members" and not isinstance(value, dict):
                    entity[key] = {str(year): value for year in years}
    return situation


@st.composite
def households(draw):
    # The CTR applicant is the family with the household's oldest member, so
    # claimants are older than their non-dependants. State Pension age is at
    # most 67 in 2025-30.
    claimant_age = draw(st.one_of(st.integers(50, 64), st.integers(68, 95)))
    non_dependants = [
        dict(
            age=draw(st.integers(18, claimant_age - 1)),
            education=draw(
                st.sampled_from(
                    ["NOT_IN_EDUCATION"] * 4 + ["TERTIARY", "UPPER_SECONDARY"]
                )
            ),
            earnings=draw(st.one_of(st.just(0.0), st.floats(0, 60_000))),
            other_income=draw(st.one_of(st.just(0.0), st.floats(0, 30_000))),
            self_employment=draw(st.one_of(st.just(0.0), st.floats(-20_000, 20_000))),
            hours=draw(st.sampled_from([0.0, 10.0, 15.9, 16.0, 35.0, 45.0])),
            income_rise=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
            approved_training=False,
        )
        for _ in range(draw(st.integers(1, 2)))
    ]
    # A dependent young person (SSCBA s.142) in the non-dependant family: in
    # full-time education (a student) or on approved training (not a student,
    # so a separate non-dependant with their own deduction).
    if draw(st.booleans()):
        training = draw(st.booleans())
        non_dependants.append(
            dict(
                age=draw(st.integers(16, 19)),
                education="NOT_IN_EDUCATION" if training else "UPPER_SECONDARY",
                earnings=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
                other_income=0.0,
                self_employment=0.0,
                hours=draw(st.sampled_from([0.0, 8.0, 16.0, 35.0])),
                income_rise=draw(st.one_of(st.just(0.0), st.floats(0, 10_000))),
                approved_training=training,
            )
        )
    return dict(
        country=draw(st.sampled_from(sorted(COUNTRIES))),
        claimant_age=claimant_age,
        claimant_disability=draw(st.sampled_from(CLAIMANT_DISABILITY)),
        benefits={
            benefit: draw(st.sampled_from([0.0, 0.0, 0.0, 1_000.0]))
            for benefit in BENEFITS
        },
        non_dependants=non_dependants,
    )


def build(population, year, raise_income=False):
    people, benunits, households_, persons = {}, {}, {}, []
    for h, household in enumerate(population):
        claimant = f"claimant_{h}"
        flag = household["claimant_disability"]
        people[claimant] = dict(
            age=household["claimant_age"],
            current_education="NOT_IN_EDUCATION",
            total_income=0.0,
            employment_income=0.0,
            self_employment_income=0.0,
            is_in_approved_training=False,
            age_started_or_accepted_current_education_or_training=1_000,
            weekly_hours=0.0,
            is_blind=flag == "is_blind",
            **{
                name: 1_000.0 if flag == name else 0.0
                for name in CLAIMANT_DISABILITY[3:]
                if name != "is_blind"
            },
        )
        persons.append(dict(household=h, benunit=2 * h, non_dependant=None))
        members = []
        for n, nd in enumerate(household["non_dependants"]):
            name = f"non_dependant_{h}_{n}"
            other = nd["other_income"] + (nd["income_rise"] if raise_income else 0)
            people[name] = dict(
                age=nd["age"],
                current_education=nd["education"],
                total_income=nd["earnings"] + other,
                employment_income=nd["earnings"],
                self_employment_income=nd["self_employment"],
                is_in_approved_training=nd["approved_training"],
                # Young people started at 16; adults' start ages don't matter.
                age_started_or_accepted_current_education_or_training=16,
                weekly_hours=nd["hours"],
                is_blind=False,
                **{
                    benefit: 0.0
                    for benefit in CLAIMANT_DISABILITY[3:]
                    if benefit != "is_blind"
                },
            )
            members.append(name)
            persons.append(dict(household=h, benunit=2 * h + 1, non_dependant=nd))
        benunits[f"claimant_unit_{h}"] = dict(
            members=[claimant],
            benunit_is_rent_liable=True,
            **{benefit: 0.0 for benefit in BENEFITS + OTHER_FAMILY_BENEFITS},
        )
        benunits[f"non_dependant_unit_{h}"] = dict(
            members=members,
            benunit_is_rent_liable=False,
            **household["benefits"],
            **{benefit: 0.0 for benefit in OTHER_FAMILY_BENEFITS},
        )
        households_[f"household_{h}"] = dict(
            members=[claimant, *members],
            country=household["country"],
            local_authority=COUNTRIES[household["country"]],
        )
    situation = dict(people=people, benunits=benunits, households=households_)
    return Simulation(situation=for_years(situation, [year])), persons


def calculate(sim, year):
    names = dict(
        person=[
            "housing_benefit_non_dep_deduction_exempt",
            "housing_benefit_individual_non_dep_deduction_eligible",
            "household_benefits_individual_non_dep_deduction",
            "council_tax_reduction_non_dep_deduction_exempt",
            "council_tax_reduction_individual_non_dep_deduction_eligible",
            "council_tax_reduction_individual_non_dep_deduction",
            "is_benunit_head",
            "is_child_or_qualifying_young_person_for_child_benefit",
        ],
        benunit=[
            "housing_benefit_non_dep_deductions",
            "housing_benefit_non_dep_deductions_claimant_exempt",
            "council_tax_reduction_non_dep_deductions",
            "universal_credit_pre_benefit_cap",
        ],
        household=[
            "council_tax_reduction_household_has_non_dep_exemption",
            "council_tax_reduction_household_has_pensioner",
        ],
    )
    return {
        name: np.asarray(sim.calculate(name, year))
        for entity in names.values()
        for name in entity
    }


def aggregate(individual, persons, couple, benunit_count, each_member):
    """Recompute family deductions from individual amounts (invariant 5): the
    claimant and partner's higher amount (both where each_member), plus each
    other member's."""
    couple_amounts, others = {}, {}
    for i, person in enumerate(persons):
        target = couple_amounts if couple[i] else others
        target.setdefault(person["benunit"], []).append(individual[i])
    own = np.array(
        [
            (sum if each_member[b] else max)(couple_amounts.get(b, [0.0]))
            + sum(others.get(b, []))
            for b in range(benunit_count)
        ]
    )
    household_of = {p["benunit"]: p["household"] for p in persons}
    totals = {}
    for b in range(benunit_count):
        totals[household_of[b]] = totals.get(household_of[b], 0.0) + own[b]
    return np.array([totals[household_of[b]] - own[b] for b in range(benunit_count)])


@PROPERTY_SETTINGS
@given(
    population=st.lists(households(), min_size=1, max_size=12),
    year=st.integers(2025, 2030),
)
@example(
    # Rare under random draws: a Welsh working-age applicant's non-dependant
    # couple on Universal Credit, both with earnings (Sch 6 para 5(3)); and
    # the Housing Benefit under-25 boundary on Income Support (reg 74(8)).
    population=[
        dict(
            country="WALES",
            claimant_age=60,
            claimant_disability=None,
            benefits={
                **dict.fromkeys(BENEFITS, 0.0),
                "universal_credit_pre_benefit_cap": 1_000.0,
            },
            non_dependants=[
                dict(
                    age=30,
                    education="NOT_IN_EDUCATION",
                    earnings=15_600.0,
                    other_income=0.0,
                    hours=35.0,
                    income_rise=0.0,
                    self_employment=0.0,
                    approved_training=False,
                ),
                dict(
                    age=28,
                    education="NOT_IN_EDUCATION",
                    earnings=1_000.0,
                    other_income=0.0,
                    hours=0.0,
                    income_rise=5_000.0,
                    self_employment=0.0,
                    approved_training=False,
                ),
            ],
        ),
        *[
            dict(
                country="ENGLAND",
                claimant_age=70,
                claimant_disability=None,
                benefits={**dict.fromkeys(BENEFITS, 0.0), "income_support": 1_000.0},
                non_dependants=[
                    dict(
                        age=age,
                        education="NOT_IN_EDUCATION",
                        earnings=0.0,
                        other_income=0.0,
                        hours=0.0,
                        income_rise=0.0,
                        self_employment=0.0,
                        approved_training=False,
                    )
                ],
            )
            for age in [24, 25]
        ],
    ],
    year=2026,
)
def test_non_dependant_deduction_invariants(population, year):
    sim, persons = build(population, year)
    r = calculate(sim, year)
    p = SYSTEM.parameters(str(year))
    hb = p.gov.dwp.housing_benefit.non_dep_deduction
    hb_lowest, hb_top = hb.amount.amounts[0] * WEEKS, hb.amount.amounts[-1] * WEEKS
    pension_age = np.repeat(
        r["council_tax_reduction_household_has_pensioner"],
        [1 + len(h["non_dependants"]) for h in population],
    )
    # Claimant or partner of each person's own family: its head, or a member
    # who is not an SSCBA s.142 child or qualifying young person.
    couple = r["is_benunit_head"].astype(bool) | ~r[
        "is_child_or_qualifying_young_person_for_child_benefit"
    ].astype(bool)

    for i, person in enumerate(persons):
        household = population[person["household"]]
        hb_deduction = r["household_benefits_individual_non_dep_deduction"][i]
        ctr_deduction = r["council_tax_reduction_individual_non_dep_deduction"][i]
        # 1. Exempt => 0.
        if r["housing_benefit_non_dep_deduction_exempt"][i]:
            assert hb_deduction == 0
        if r["council_tax_reduction_non_dep_deduction_exempt"][i]:
            assert ctr_deduction == 0
        nd = person["non_dependant"]
        if nd is None:
            continue
        # 9. The exemptions, read straight from the inputs.
        # A family award belongs to its claimant and partner; a self-employed
        # loss counts as nil earnings (UC reg 57(2)).
        on = {b: bool(couple[i]) and household["benefits"][b] > 0 for b in BENEFITS}
        student = nd["education"] != "NOT_IN_EDUCATION"
        # Inputs are stored as float32, so a tiny draw can underflow to nil.
        earned = (
            max(0.0, float(np.float32(nd["earnings"])))
            + max(0.0, float(np.float32(nd["self_employment"])))
            > 0
        )
        uc_without_earnings = on["universal_credit_pre_benefit_cap"] and not earned
        hb_exempt = (
            student
            or on["pension_credit"]
            or (
                nd["age"] < 25
                and (on["income_support"] or on["jsa_income"] or uc_without_earnings)
            )
        )
        assert bool(r["housing_benefit_non_dep_deduction_exempt"][i]) == hb_exempt
        national = household["country"] != "ENGLAND" or pension_age[i]
        ctr_exempt = (
            student
            or any(
                on[b]
                for b in [
                    "income_support",
                    "jsa_income",
                    "esa_income",
                    "pension_credit",
                ]
            )
            or (national and uc_without_earnings)
        )
        assert (
            bool(r["council_tax_reduction_non_dep_deduction_exempt"][i]) == ctr_exempt
        )
        # 2-3. Housing Benefit bounds and the not-in-work amount.
        if (
            r["housing_benefit_individual_non_dep_deduction_eligible"][i]
            and not r["housing_benefit_non_dep_deduction_exempt"][i]
        ):
            assert hb_lowest - 0.01 <= hb_deduction <= hb_top + 0.01
            # Reg 6(6): on IS, JSA(IB) or ESA(IR) is not remunerative work.
            if (
                nd["hours"] < hb.remunerative_work_hours
                or on["income_support"]
                or on["jsa_income"]
                or on["esa_income"]
            ):
                assert hb_deduction == pytest.approx(hb_lowest, abs=0.01)
        # 2-3. Council Tax Reduction bounds and the not-in-work amount.
        country = household["country"]
        if not national:
            assert ctr_deduction == 0
        elif (
            r["council_tax_reduction_individual_non_dep_deduction_eligible"][i]
            and not r["council_tax_reduction_non_dep_deduction_exempt"][i]
        ):
            scale = p.gov.local_authorities
            for part in CTR_SCALES[country].split("."):
                scale = getattr(scale, part)
            lowest = scale.amount.amounts[0] * WEEKS
            top = scale.amount.amounts[-1] * WEEKS
            assert lowest - 0.01 <= ctr_deduction <= top + 0.01
            if nd["hours"] < scale.remunerative_work_hours:
                assert ctr_deduction == pytest.approx(lowest, abs=0.01)

    benunit_count = 2 * len(population)
    # 4-5. Housing Benefit aggregation and the claimant exemption.
    expected_hb = aggregate(
        r["household_benefits_individual_non_dep_deduction"],
        persons,
        couple,
        benunit_count,
        [False] * benunit_count,
    )
    expected_hb = np.where(
        r["housing_benefit_non_dep_deductions_claimant_exempt"], 0, expected_hb
    )
    np.testing.assert_allclose(
        r["housing_benefit_non_dep_deductions"], expected_hb, atol=0.01
    )
    # 4-5. Council Tax Reduction aggregation and the applicant exemption.
    welsh_working_age = [
        population[b // 2]["country"] == "WALES"
        and not r["council_tax_reduction_household_has_pensioner"][b // 2]
        and r["universal_credit_pre_benefit_cap"][b] > 0
        for b in range(benunit_count)
    ]
    expected_ctr = aggregate(
        r["council_tax_reduction_individual_non_dep_deduction"],
        persons,
        couple,
        benunit_count,
        welsh_working_age,
    )
    household_exempt = np.repeat(
        r["council_tax_reduction_household_has_non_dep_exemption"], 2
    )
    expected_ctr = np.where(household_exempt, 0, expected_ctr)
    np.testing.assert_allclose(
        r["council_tax_reduction_non_dep_deductions"], expected_ctr, atol=0.01
    )

    # 6. Raising non-dependants' incomes never lowers a deduction.
    raised, _ = build(population, year, raise_income=True)
    s = calculate(raised, year)
    for name in [
        "household_benefits_individual_non_dep_deduction",
        "council_tax_reduction_individual_non_dep_deduction",
        "housing_benefit_non_dep_deductions",
        "council_tax_reduction_non_dep_deductions",
    ]:
        assert np.all(s[name] >= r[name] - 1e-3), name


def first_income_at_or_above(threshold):
    """The smallest float32 annual income (the input's storage type) whose
    weekly value, computed as the model does (the benefit-unit sum returns
    float64, then divided by 52), is at least the threshold."""

    def weekly(annual):
        return float(np.float32(annual)) / WEEKS

    income = np.float32(threshold * WEEKS)
    while weekly(income) < threshold:
        income = np.nextafter(income, np.float32(np.inf))
    while weekly(np.nextafter(income, np.float32(-np.inf))) >= threshold:
        income = np.nextafter(income, np.float32(-np.inf))
    return income


SCALES = [
    ("HOUSING_BENEFIT", range(2019, 2031)),
    ("ENGLAND", range(2015, 2031)),
    ("WALES", range(2015, 2031)),
    ("SCOTLAND", range(2015, 2031)),
]


@pytest.mark.parametrize("scale_name, years", SCALES, ids=[s for s, _ in SCALES])
def test_band_edges_are_inclusive(scale_name, years):
    """Invariant 7: every lower edge, every year, both schemes."""
    country = "ENGLAND" if scale_name == "HOUSING_BENEFIT" else scale_name
    edges_by_year = {}
    for year in years:
        p = SYSTEM.parameters(str(year))
        if scale_name == "HOUSING_BENEFIT":
            scale = p.gov.dwp.housing_benefit.non_dep_deduction.amount
        else:
            scale = p.gov.local_authorities
            for part in CTR_SCALES[scale_name].split("."):
                scale = getattr(scale, part)
            scale = scale.amount
        edges_by_year[year] = list(
            zip(scale.thresholds[1:], scale.amounts[1:], scale.amounts[:-1])
        )
    count = max(len(edges) for edges in edges_by_year.values())
    people, benunits, households_ = {}, {}, {}
    for k in range(2 * count):
        claimant, non_dependant = f"claimant_{k}", f"non_dependant_{k}"
        incomes = {}
        for year, edges in edges_by_year.items():
            threshold, _, _ = edges[k // 2]
            at_edge = first_income_at_or_above(threshold)
            incomes[str(year)] = float(
                at_edge if k % 2 == 0 else np.nextafter(at_edge, np.float32(-np.inf))
            )
        people[claimant] = dict(age=80, current_education="NOT_IN_EDUCATION")
        people[non_dependant] = dict(
            age=40,
            current_education="NOT_IN_EDUCATION",
            weekly_hours={str(y): 35.0 for y in years},
            total_income=incomes,
            employment_income={str(y): 0.0 for y in years},
        )
        benunits[f"claimant_unit_{k}"] = dict(
            members=[claimant],
            benunit_is_rent_liable={str(y): True for y in years},
            **{b: {str(y): 0.0 for y in years} for b in BENEFITS},
        )
        benunits[f"non_dependant_unit_{k}"] = dict(
            members=[non_dependant],
            benunit_is_rent_liable={str(y): False for y in years},
            **{b: {str(y): 0.0 for y in years} for b in BENEFITS},
        )
        households_[f"household_{k}"] = dict(
            members=[claimant, non_dependant],
            country=country,
            local_authority=COUNTRIES[country],
        )
    sim = Simulation(
        situation=for_years(
            dict(people=people, benunits=benunits, households=households_), years
        )
    )
    variable = (
        "household_benefits_individual_non_dep_deduction"
        if scale_name == "HOUSING_BENEFIT"
        else "council_tax_reduction_individual_non_dep_deduction"
    )
    for year, edges in edges_by_year.items():
        deductions = np.asarray(sim.calculate(variable, year))[1::2] / WEEKS
        for k, (threshold, amount, below) in enumerate(edges):
            assert deductions[2 * k] == pytest.approx(amount, abs=1e-4), (
                year,
                threshold,
            )
            assert deductions[2 * k + 1] == pytest.approx(below, abs=1e-4), (
                year,
                threshold,
            )


def test_ctr_scales_match_enacted_sums():
    """Invariant 8: the parameters reproduce the enacted table."""
    fixture = yaml.safe_load(FIXTURE.read_text())
    for scheme, entry in fixture.items():
        for year, row in entry["years"].items():
            # PolicyEngine UK reads parameters at 30 April from 2015; earlier
            # years are read at that date directly.
            instant = str(year) if year >= 2015 else f"{year}-04-30"
            node = SYSTEM.parameters(instant)
            for part in entry["parameter"].split("."):
                node = getattr(node, part)
            assert list(node.thresholds) == pytest.approx(row["thresholds"]), (
                scheme,
                year,
            )
            assert list(node.amounts) == pytest.approx(row["amounts"]), (scheme, year)
