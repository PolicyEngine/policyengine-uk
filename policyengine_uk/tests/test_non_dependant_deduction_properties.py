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
4. If the claimant or partner is blind or receives a qualifying disability
   benefit (read from the generated inputs, and checked against the model's
   flags), the claimant family's deductions are 0.
5. Aggregation: a family's deductions are the sum, over the other families in
   the household, of their claimant and partner's higher amount (both amounts
   for a Welsh working-age applicant's non-dependant couple whose own
   Universal Credit award assesses either member; another member's award as
   a single claimant leaves the couple one deduction) plus each other
   member's, recomputed here from the individual amounts, times the family's
   share of the rent (Housing Benefit, reg 74(5)) or of the council tax
   liability (CTR, Sch 1 para 8(5)).
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
   scheme, on Universal Credit without earned income, or an adult for whom
   someone else is entitled to child benefit, which needs a claim (LGFA 1992
   Sch 1 para 3). In Scotland's working-age scheme from April 2022, also
   anyone whose partner is on IS, JSA(IB) or ESA(IR) and who is not on
   Universal Credit (SSI 2021/249 reg 90(8)(a), reg 4(1)). IS, JSA(IB),
   ESA(IR) and SPC count only for the person they are payable to, read from
   the model's is_on_* status (HB Regs 2006 reg 2(1), (3), (3A)); where the
   claimant or partner reports the award, or no one does, that is the
   reporter or the benefit unit's head, which the test checks. Universal
   Credit counts for the claimants it assesses: the members the generated
   is_uc_claimant flags name (by default the claimant and partner), the two
   eldest where more are flagged, which the test checks. Earned income is
   Universal Credit's own calculation (invariant 13).
10. (In test_rent_of_sharers_boarders_and_lodgers_properties.py.)
11. Banding: a non-dependant in remunerative work who is neither exempt nor
   on IS, JSA(IB) or ESA(IR) pays the amount of the band whose lower edge is
   the highest not above their normal gross weekly income, computed here from
   the generated inputs: earnings, statutory sick, maternity and paternity
   pay, self-employed profit with a loss as nil, and other investment income;
   for the claimant or partner of the non-dependant's family, the couple's
   sum plus the family's IS, JSA(IB), ESA(IR) and Pension Credit, and its
   Universal Credit where the award assesses either of them. Another member
   who claims Universal Credit alone is banded on their own income and that
   award. Incomes within a penny a week of an edge are skipped, since the
   inputs are stored as float32.
12. Differential: the after-cap Universal Credit used in a non-dependant
   family's gross income equals the model's universal_credit for a family
   with no Housing Benefit, no Maternity Allowance and no deductions from
   its award, under current law and under an 85% protected minimum floor;
   and it reads a stored universal_credit, cap reduction or welfare-benefit
   total, and a universal_credit formula a reform replaces.
13. Differential: the Universal Credit exemption's earned-income test agrees
   with Universal Credit's own calculation (uc_individual_earned_income)
   across employment expenses, trading losses, company income attributed to
   its owner, pension contributions and the minimum income floor of single
   claimants and couples; and it agrees with the inputs where they settle it
   without the tax and National Insurance calculation.
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
REPORTED = {
    "income_support": "income_support_reported",
    "jsa_income": "jsa_income_reported",
    "esa_income": "esa_income_reported",
    "pension_credit": "pension_credit_reported",
}
IS_ON = {
    "income_support": "is_on_income_support",
    "jsa_income": "is_on_income_based_jsa",
    "esa_income": "is_on_income_related_esa",
    "pension_credit": "is_on_pension_credit",
}
STATUTORY_PAY = [
    "statutory_sick_pay",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
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
            statutory_pay={
                name: draw(st.one_of(st.just(0.0), st.floats(0, 10_000)))
                for name in STATUTORY_PAY
            },
            pension_contributions=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
            startup_period=draw(st.booleans()),
            hours=draw(st.sampled_from([0.0, 10.0, 15.9, 16.0, 35.0, 45.0])),
            income_rise=draw(st.one_of(st.just(0.0), st.floats(0, 40_000))),
            approved_training=False,
        )
        for _ in range(draw(st.integers(1, 2)))
    ]
    # A young person aged 16-19 in the non-dependant family: in full-time
    # education (a student) or on approved training (not a student). Whether
    # they are the family's claimant or partner is read from the model's
    # is_claimant_or_partner.
    if draw(st.booleans()):
        training = draw(st.booleans())
        non_dependants.append(
            dict(
                age=draw(st.integers(16, 19)),
                education="NOT_IN_EDUCATION" if training else "UPPER_SECONDARY",
                earnings=draw(st.one_of(st.just(0.0), st.floats(0, 20_000))),
                other_income=0.0,
                self_employment=0.0,
                statutory_pay=dict.fromkeys(STATUTORY_PAY, 0.0),
                pension_contributions=0.0,
                startup_period=False,
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
        # Which adult non-dependant reports IS, JSA(IB), ESA(IR) and SPC, if
        # anyone does.
        reporter=draw(st.sampled_from([None, 0, 1])),
        # Explicit is_uc_claimant flags for the non-dependants, by position,
        # or None to leave the claimant and partner as the claimants. A flag
        # on the young person alone makes them a single claimant beside the
        # couple.
        uc_claimants=draw(
            st.one_of(st.none(), st.lists(st.booleans(), min_size=3, max_size=3))
        ),
        claims_child_benefit=draw(st.sampled_from([True, True, False])),
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
            reports = household.get("reporter") == n
            people[name] = dict(
                age=nd["age"],
                current_education=nd["education"],
                employment_income=nd["earnings"],
                other_investment_income=other,
                self_employment_income=nd["self_employment"],
                **nd.get("statutory_pay", dict.fromkeys(STATUTORY_PAY, 0.0)),
                pension_contributions=nd.get("pension_contributions", 0.0),
                uc_is_in_startup_period=nd.get("startup_period", False),
                **{
                    reported: household["benefits"][benefit] if reports else 0.0
                    for benefit, reported in REPORTED.items()
                },
                # Held at zero so the oracle knows each person's gross income.
                state_pension=0.0,
                carers_allowance=0.0,
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
            if household.get("uc_claimants") is not None:
                people[name]["is_uc_claimant"] = household["uc_claimants"][n]
            members.append(name)
            persons.append(
                dict(household=h, benunit=2 * h + 1, non_dependant=nd, position=n)
            )
        benunits[f"claimant_unit_{h}"] = dict(
            members=[claimant],
            benunit_is_rent_liable=True,
            **{benefit: 0.0 for benefit in BENEFITS + OTHER_FAMILY_BENEFITS},
        )
        benunits[f"non_dependant_unit_{h}"] = dict(
            members=members,
            benunit_is_rent_liable=False,
            would_claim_child_benefit=household.get("claims_child_benefit", True),
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
            "is_claimant_or_partner",
            "is_uc_assessed_claimant",
            "is_qualifying_young_person_for_child_benefit",
            "uc_individual_earned_income",
            "is_on_income_support",
            "is_on_income_based_jsa",
            "is_on_income_related_esa",
            "is_on_pension_credit",
        ],
        benunit=[
            "housing_benefit_non_dep_deductions",
            "housing_benefit_non_dep_deductions_claimant_exempt",
            "council_tax_reduction_non_dep_deductions",
            "universal_credit_pre_benefit_cap",
            "council_tax_reduction_applicant_has_non_dep_exemption",
            "council_tax_reduction_pensioner",
            "council_tax_reduction_joint_liability_share",
            "share_of_household_rent",
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
    # Each applicant's scheme follows its own family; the applicant is each
    # household's claimant family (benefit units 0, 2, 4, ...).
    applicant_pensioner = r["council_tax_reduction_pensioner"].astype(bool)[0::2]
    pension_age = np.repeat(
        applicant_pensioner,
        [1 + len(h["non_dependants"]) for h in population],
    )
    # Claimant or partner of each person's own family (SSCBA s.137 couple).
    couple = r["is_claimant_or_partner"].astype(bool)
    members_of = {}
    for i, person in enumerate(persons):
        members_of.setdefault(person["benunit"], []).append(i)
    # Universal Credit's claimants: the members is_uc_claimant flags (by
    # default the claimant and partner), the two eldest where inputs flag
    # more (WRA 2012 ss. 2(1), 40), in the order entered at equal ages.
    assessed = r["is_uc_assessed_claimant"].astype(bool)
    for members in members_of.values():
        household = population[persons[members[0]]["household"]]
        flags = household.get("uc_claimants")

        def flagged(j):
            if flags is None or persons[j]["non_dependant"] is None:
                return bool(couple[j])
            return flags[persons[j]["position"]]

        def age(j):
            nd = persons[j]["non_dependant"]
            return household["claimant_age"] if nd is None else nd["age"]

        eldest = sorted(filter(flagged, members), key=lambda j: -age(j))[:2]
        assert sorted(j for j in members if assessed[j]) == sorted(eldest)
    # Whether a family's Universal Credit is the couple's own: it assesses
    # the claimant or partner.
    couple_claims_universal_credit = {
        b: any(couple[j] and assessed[j] for j in members)
        for b, members in members_of.items()
    }

    def payee_of(i, benefit):
        """The award's payee: the member who reports it, or the head."""
        person = persons[i]
        household = population[person["household"]]
        reporter = household.get("reporter")
        reported = (
            person["non_dependant"] is not None
            and reporter is not None
            and reporter < len(household["non_dependants"])
            and household["benefits"][benefit] > 0
        )
        if reported:
            return person["position"] == reporter
        return bool(r["is_benunit_head"][i])

    f32 = np.float32

    def own_gross(j):
        """A person's own gross income from the generated inputs (invariant
        11): a self-employment loss counts as nil."""
        nd_j = persons[j]["non_dependant"]
        if nd_j is None:
            return 0.0
        return float(
            f32(nd_j["earnings"])
            + sum(
                f32(nd_j.get("statutory_pay", {}).get(name, 0.0))
                for name in STATUTORY_PAY
            )
            + max(f32(0), f32(nd_j["self_employment"]))
            + f32(nd_j["other_income"])
        )

    def band_amount(scale, weekly):
        """The amount of the band whose lower edge is the highest not above
        weekly income, or None within a penny of an edge."""
        if any(abs(weekly - t) < 0.01 for t in scale.thresholds[1:]):
            return None
        index = max(k for k, t in enumerate(scale.thresholds) if t <= weekly)
        return scale.amounts[index] * WEEKS

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
        # IS, JSA(IB), ESA(IR) and SPC count for their payee (HB reg 2(1),
        # (3)-(3A)): the model's is_on_* status. Where the reporter, if any, is
        # the claimant or partner, that is the reporter, or the benefit unit's
        # head where none reports. Universal Credit counts for the claimants
        # it assesses.
        on = {b: bool(r[IS_ON[b]][i]) for b in REPORTED}
        reporter = household.get("reporter")
        reporter_index = (
            None
            if reporter is None or reporter >= len(household["non_dependants"])
            else members_of[person["benunit"]][reporter]
        )
        # Pension Credit's payee must also have reached the qualifying age
        # (SPCA 2002 s.1(2)(b)), which payee_of doesn't model.
        if reporter_index is None or couple[reporter_index]:
            for b in ["income_support", "jsa_income", "esa_income"]:
                assert on[b] == (payee_of(i, b) and household["benefits"][b] > 0), (
                    b,
                    i,
                )
        on["universal_credit_pre_benefit_cap"] = (
            bool(assessed[i])
            and household["benefits"]["universal_credit_pre_benefit_cap"] > 0
        )
        student = nd["education"] != "NOT_IN_EDUCATION"
        # Earned income is Universal Credit's own calculation (HB reg 74(11),
        # CTR Sch 1 para 8(11A) and equivalents: UC Regs 2013 reg 52), which
        # invariant 13 checks against the inputs.
        earned = r["uc_individual_earned_income"][i] > 0
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
        legacy = ["income_support", "jsa_income", "esa_income"]
        on_legacy = any(on[b] for b in legacy)
        # Scotland's working-age scheme (SSI 2021/249, from April 2022): a
        # non-dependant who is, or whose partner is, on IS, JSA(IB) or ESA(IR)
        # and who is not on Universal Credit.
        if household["country"] == "SCOTLAND" and not pension_age[i]:
            couple_on_legacy = bool(couple[i]) and any(
                couple[j] and any(r[IS_ON[b]][j] for b in legacy)
                for j in members_of[person["benunit"]]
            )
            qualifying = (on_legacy or couple_on_legacy) and not on[
                "universal_credit_pre_benefit_cap"
            ]
        else:
            qualifying = on_legacy
        ctr_exempt = (
            student
            or qualifying
            or on["pension_credit"]
            or (national and uc_without_earnings)
            # LGFA 1992 Sch 1 para 3: an adult in someone else's family for
            # whom child benefit is claimed.
            or (
                nd["age"] >= 18
                and bool(r["is_qualifying_young_person_for_child_benefit"][i])
                and not couple[i]
                and household.get("claims_child_benefit", True)
            )
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

        # 11. Banding on gross income computed from the inputs. Income-based
        # JSA and income-related ESA count only where the claimant or partner
        # reports them, or no one does.
        couple_awards = (
            ["jsa_income", "esa_income"]
            if reporter_index is None or couple[reporter_index]
            else []
        )
        family_awards = sum(
            household["benefits"][b]
            for b in ["income_support", "pension_credit", *couple_awards]
        )
        # Universal Credit is the income of the claimants it assesses: the
        # couple's, or a single claimant's beside it.
        universal_credit = household["benefits"]["universal_credit_pre_benefit_cap"]
        couple_claims = couple_claims_universal_credit[person["benunit"]]
        if couple[i]:
            weekly = (
                sum(own_gross(j) for j in members_of[person["benunit"]] if couple[j])
                + family_awards
                + (universal_credit if couple_claims else 0.0)
            ) / WEEKS
        else:
            weekly = (
                own_gross(i)
                + (universal_credit if assessed[i] and not couple_claims else 0.0)
            ) / WEEKS
        if (
            r["housing_benefit_individual_non_dep_deduction_eligible"][i]
            and nd["hours"] >= hb.remunerative_work_hours
            and not (on["income_support"] or on["jsa_income"] or on["esa_income"])
        ):
            expected = band_amount(hb.amount, weekly)
            if expected is not None:
                assert hb_deduction == pytest.approx(expected, abs=0.01), (i, weekly)
        if (
            national
            and r["council_tax_reduction_individual_non_dep_deduction_eligible"][i]
            and not r["council_tax_reduction_non_dep_deduction_exempt"][i]
            and nd["hours"] >= scale.remunerative_work_hours
            and not qualifying
        ):
            expected = band_amount(scale.amount, weekly)
            if expected is not None:
                assert ctr_deduction == pytest.approx(expected, abs=0.01), (i, weekly)

    benunit_count = 2 * len(population)
    # 4-5. Housing Benefit aggregation and the claimant exemption.
    expected_hb = aggregate(
        r["household_benefits_individual_non_dep_deduction"],
        persons,
        couple,
        benunit_count,
        [False] * benunit_count,
    )
    # 4. The claimant exemption, from the generated disability inputs: only
    # the claimant family's claimant can be blind or on a qualifying benefit.
    disabled = np.array([h["claimant_disability"] is not None for h in population])
    claimant_exempt = np.repeat(disabled, 2) & (np.arange(benunit_count) % 2 == 0)
    np.testing.assert_array_equal(
        r["housing_benefit_non_dep_deductions_claimant_exempt"].astype(bool),
        claimant_exempt,
    )
    expected_hb = np.where(
        claimant_exempt, 0, expected_hb * r["share_of_household_rent"]
    )
    np.testing.assert_allclose(
        r["housing_benefit_non_dep_deductions"], expected_hb, atol=0.01
    )
    # 4-5. Council Tax Reduction aggregation and the applicant exemption.
    welsh_working_age = [
        population[b // 2]["country"] == "WALES"
        and not applicant_pensioner[b // 2]
        and couple_claims_universal_credit[b]
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
    # The applicant is the claimant family (its member is the oldest).
    np.testing.assert_array_equal(
        r["council_tax_reduction_applicant_has_non_dep_exemption"].astype(bool),
        claimant_exempt,
    )
    expected_ctr = np.where(
        claimant_exempt,
        0,
        expected_ctr * r["council_tax_reduction_joint_liability_share"],
    )
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
            housing_benefit_non_dep_gross_income=incomes,
            council_tax_reduction_non_dep_gross_income=incomes,
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


def capped_universal_credit_families(families, year, **extra):
    """One household per family: the generated awards, no Housing Benefit,
    no Maternity Allowance and no deductions from the award."""
    people, benunits, households_ = {}, {}, {}
    for f, family in enumerate(families):
        members = [f"adult_{f}_{k}" for k in range(2 if family["couple"] else 1)]
        for k, name in enumerate(members):
            people[name] = dict(
                age=30 - k,
                jsa_contrib=family["jsa_contrib"] if k == 0 else 0.0,
                esa_contrib=family["esa_contrib"] if k == 0 else 0.0,
                maternity_allowance=0.0,
            )
        benunits[f"family_{f}"] = dict(
            members=members,
            **{
                key: family[key]
                for key in [
                    "universal_credit_pre_benefit_cap",
                    "child_benefit",
                    "child_tax_credit",
                    "uc_benefit_cap",
                    "uc_childcare_element",
                ]
            },
            income_support=0.0,
            jsa_income=0.0,
            esa_income=0.0,
            housing_benefit_pre_benefit_cap=0.0,
            uc_deduction_rate=0.0,
            uc_deductions=0.0,
            **extra,
        )
        households_[f"household_{f}"] = dict(members=members, country="ENGLAND")
    return for_years(
        dict(people=people, benunits=benunits, households=households_), [year]
    )


def capped_universal_credit(sim, year):
    from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
        universal_credit_after_benefit_cap,
    )

    return universal_credit_after_benefit_cap(
        sim.populations["benunit"], year, sim.tax_benefit_system.parameters
    )


CAPPED_FAMILY = st.fixed_dictionaries(
    dict(
        couple=st.booleans(),
        universal_credit_pre_benefit_cap=st.one_of(st.just(0.0), st.floats(0, 40_000)),
        child_benefit=st.sampled_from([0.0, 1_500.0, 5_000.0]),
        child_tax_credit=st.sampled_from([0.0, 3_000.0]),
        uc_benefit_cap=st.sampled_from([14_753.0, 22_020.0, 25_323.0]),
        uc_childcare_element=st.sampled_from([0.0, 2_000.0, 12_000.0]),
        jsa_contrib=st.sampled_from([0.0, 4_000.0]),
        esa_contrib=st.sampled_from([0.0, 5_000.0]),
    )
)
ONE_CAPPED_FAMILY = dict(
    couple=False,
    universal_credit_pre_benefit_cap=20_000.0,
    child_benefit=0.0,
    child_tax_credit=0.0,
    uc_benefit_cap=14_753.0,
    uc_childcare_element=0.0,
    jsa_contrib=0.0,
    esa_contrib=0.0,
)


@PROPERTY_SETTINGS
@given(
    families=st.lists(CAPPED_FAMILY, min_size=1, max_size=8),
    year=st.integers(2025, 2030),
    protected_floor=st.sampled_from([0.0, 0.85]),
)
@example(families=[ONE_CAPPED_FAMILY], year=2025, protected_floor=0.85)
def test_capped_universal_credit_matches_the_model(families, year, protected_floor):
    """Invariant 12: the after-cap Universal Credit counted in a
    non-dependant family's gross income equals universal_credit for a family
    with no Housing Benefit, Maternity Allowance or deductions, with or
    without a protected minimum floor."""
    reform = (
        {
            "gov.dwp.universal_credit.deductions.protected_floor": {
                f"{year}-01-01.{year}-12-31": protected_floor
            }
        }
        if protected_floor
        else None
    )
    sim = Simulation(
        situation=capped_universal_credit_families(families, year), reform=reform
    )
    np.testing.assert_allclose(
        capped_universal_credit(sim, year),
        sim.calculate("universal_credit", year),
        atol=0.01,
    )


def test_capped_universal_credit_reads_stored_and_replaced_values():
    """Invariant 12: a stored award, cap reduction or welfare-benefit total,
    and a replaced universal_credit formula, reach the gross income. The
    family's Universal Credit before the cap is 20,000 against a 14,753 cap."""
    from policyengine_core.reforms import Reform
    from policyengine_core.simulations import Simulation as CoreSimulation

    from policyengine_uk.variables.gov.dwp.universal_credit.universal_credit import (
        universal_credit as current_law,
    )

    year = 2025
    for stored, expected in [
        (dict(), 14_753),
        (dict(universal_credit=15_000.0), 15_000),
        (dict(uc_benefit_cap_reduction=0.0), 20_000),
        (dict(uc_benefit_cap_reduction_after_floor=1_000.0), 19_000),
        (dict(benefit_cap_welfare_benefits=10_000.0), 20_000),
    ]:
        sim = Simulation(
            situation=capped_universal_credit_families(
                [ONE_CAPPED_FAMILY], year, **stored
            )
        )
        helper = capped_universal_credit(sim, year)
        assert helper == pytest.approx([expected], abs=0.01), stored
        assert helper == pytest.approx(
            sim.calculate("universal_credit", year), abs=0.01
        ), stored

    constant_award = type(
        "universal_credit",
        (current_law,),
        dict(formula=lambda benunit, period, parameters: benunit.filled_array(12_345)),
    )

    class ConstantAward(Reform):
        def apply(self):
            self.update_variable(constant_award)

    sim = CoreSimulation(
        tax_benefit_system=ConstantAward(SYSTEM),
        situation=capped_universal_credit_families([ONE_CAPPED_FAMILY], year),
        default_input_period=year,
        default_calculation_period=year,
    )
    assert capped_universal_credit(sim, year) == pytest.approx([12_345], abs=0.01)


# Earned-income cases for invariant 13. Each sets the person's earnings
# inputs; "settled" is what the inputs alone say, where they say it without
# the tax and National Insurance calculation: no earnings left after
# expenses, pension contributions and trading losses (False), or a small
# positive amount no deduction can remove (True).
EARNINGS = {
    "none": (dict(), False),
    "wages": (dict(employment_income=1_000.0), True),
    "wages_cancelled_by_expenses": (
        dict(employment_income=1_000.0, employment_expenses=1_000.0),
        False,
    ),
    "wages_partly_cancelled_by_expenses": (
        dict(employment_income=1_000.0, employment_expenses=500.0),
        True,
    ),
    "wages_into_pension": (
        dict(employment_income=1_000.0, employee_pension_contributions=1_000.0),
        None,
    ),
    "profit": (dict(self_employment_income=1_000.0), None),
    "profit_cancelled_by_loss": (
        dict(self_employment_income=1_000.0, trading_loss=1_000.0),
        None,
    ),
    "loss": (dict(self_employment_income=-500.0), None),
    "company_income": (
        dict(
            stands_as_sole_owner_or_partner_of_company=True,
            owned_company_carries_on_trade=True,
            owned_company_income_share=1_000.0,
        ),
        True,
    ),
    "company_income_without_owner_treatment": (
        dict(owned_company_carries_on_trade=True, owned_company_income_share=1_000.0),
        False,
    ),
    "high_wages": (dict(employment_income=30_000.0), True),
}


@PROPERTY_SETTINGS
@given(
    families=st.lists(
        st.lists(
            st.fixed_dictionaries(
                dict(
                    age=st.integers(18, 89),
                    earnings=st.sampled_from(sorted(EARNINGS)),
                    # None leaves the minimum income floor to the model.
                    floor_applies=st.sampled_from([None, None, True, False]),
                )
            ),
            min_size=1,
            max_size=2,
        ),
        min_size=1,
        max_size=6,
    ),
    year=st.integers(2025, 2030),
)
@example(
    # A couple's floor: the partner's earnings meet the couple threshold, so
    # the floor doesn't apply to the other member (UC Regs 2013 reg 62(3)).
    families=[
        [
            dict(age=24, earnings="none", floor_applies=True),
            dict(age=30, earnings="high_wages", floor_applies=False),
        ],
        [dict(age=24, earnings="none", floor_applies=True)],
    ],
    year=2026,
)
def test_earned_income_exemption_reads_universal_credit(families, year):
    """Invariant 13: the Universal Credit exemption's earned-income test is
    Universal Credit's own calculation (HB Regs 2006 reg 74(8)(b), (11); WSI
    2013/3029 Sch 1 para 3(8)(c), (10))."""
    people, benunits, households_, cases = {}, {}, {}, []
    for f, family in enumerate(families):
        claimant = f"claimant_{f}"
        people[claimant] = dict(age=90, current_education="NOT_IN_EDUCATION")
        cases.append(None)
        members = []
        for k, member in enumerate(family):
            name = f"member_{f}_{k}"
            inputs, settled = EARNINGS[member["earnings"]]
            people[name] = dict(
                age=member["age"],
                current_education="NOT_IN_EDUCATION",
                weekly_hours=0.0,
                **inputs,
            )
            if member["floor_applies"] is not None:
                people[name]["uc_mif_applies"] = member["floor_applies"]
                people[name]["uc_minimum_income_floor"] = 10_000.0
            members.append(name)
            cases.append((member, settled))
        no_awards = {benefit: 0.0 for benefit in BENEFITS + OTHER_FAMILY_BENEFITS}
        benunits[f"claimant_unit_{f}"] = dict(
            members=[claimant], benunit_is_rent_liable=True, **no_awards
        )
        benunits[f"family_{f}"] = dict(
            members=members,
            benunit_is_rent_liable=False,
            **{**no_awards, "universal_credit_pre_benefit_cap": 1_000.0},
        )
        households_[f"household_{f}"] = dict(
            members=[claimant, *members],
            country="WALES",
            local_authority=COUNTRIES["WALES"],
        )
    sim = Simulation(
        situation=for_years(
            dict(people=people, benunits=benunits, households=households_), [year]
        )
    )
    earned = np.asarray(sim.calculate("uc_individual_earned_income", year)) > 0
    claimant_ = np.asarray(sim.calculate("is_uc_assessed_claimant", year))
    floor = np.asarray(sim.calculate("uc_mif_applies", year))
    hb_exempt = np.asarray(
        sim.calculate("housing_benefit_non_dep_deduction_exempt", year)
    )
    ctr_exempt = np.asarray(
        sim.calculate("council_tax_reduction_non_dep_deduction_exempt", year)
    )
    for i, case in enumerate(cases):
        if case is None:
            continue
        member, settled = case
        assert claimant_[i]
        # The predicate is Universal Credit's earned income: the Welsh
        # pensioner scheme at any age, Housing Benefit under 25.
        assert bool(ctr_exempt[i]) == (not earned[i]), (i, member)
        assert bool(hb_exempt[i]) == (member["age"] < 25 and not earned[i]), (i, member)
        # Where the inputs settle it, and the floor doesn't apply.
        if settled is not None and not floor[i]:
            assert bool(earned[i]) == settled, (i, member)
