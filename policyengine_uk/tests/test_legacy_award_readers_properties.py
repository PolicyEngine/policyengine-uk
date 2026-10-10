"""Readers of the legacy income-related awards follow the claimant and partner.

Income-related ESA, income-based JSA and Income Support are awarded to a
claimant for themselves and their partner. Each means test or passport that
reads them names the claimant (or applicant, or person claiming) and partner,
the child's parent, or the person themselves:

- Housing Benefit and council tax reduction income: SSCBA 1992 s.136(1), HB
  Regs 2006 reg 25(1); CTR (Prescribed Requirements) (England) Regs 2012
  Sch 1 para 11.
- The Housing Benefit passport, which disregards the earnings, income and
  capital of a claimant on Income Support, income-based JSA or income-related
  ESA: HB Regs 2006 Sch 4 para 12, Sch 5 para 4 and Sch 6 para 5.
- The working-age council tax reduction passport and non-dependant
  exemption: CTR (Default Scheme) (England) Regs 2012, Schedule.
- The tax credit income test: TCA 2002 s.7(2), SI 2002/2008 reg 4.
- Scottish Child Payment: SSI 2020/351 reg 18(e)-(f).
- Targeted childcare: SI 2014/2147 reg 1(2).
- Maintenance loans for students entitled to benefits: SI 2011/1986 reg
  71(1)(h)(iii), through reg 61(2)(b) and HB Regs 2006 reg 56(2)(a) (the
  student is on the award) and (c) (the student's applicable amount would
  include a disability or severe disability premium).

A member of the benefit unit who is neither the claimant, the partner nor a
child or young person they are responsible for (for example a non-dependent
adult) claims in their own right, so:

- adding such a member, whatever Income Support, income-based JSA or
  income-related ESA they report, never changes any of these readers for the
  claimant's family or for its existing members;
- the claimant-or-partner awards are bounded by the benefit-unit awards
  (0 <= claimant_or_partner_esa_income <= esa_income, likewise for JSA) and
  equal them when no other member reports an award;
- the claimant-or-partner awards are the award on the claimant's and
  partner's reports after tariff income, within the capital limit, and only
  while the benefit unit passes the remunerative work screen
  (esa_income_eligible and jsa_income_eligible, read independently from the
  law in legacy_award_work_reference);
- a person is on an award exactly when they are the payee of their couple's
  positive award (the claimant or partner who reports it, or the claimant)
  or, for anyone else, when their own claim passes: they are not engaged in
  remunerative work as its claimant (for ESA, earnings above the exempt work
  limits; for JSA, 16 hours a week or more) and the award on their own report
  alone is positive after tariff income from the household's capital and
  within the capital limit (Income Support: when they report it).

Adults, including the adult outside the couple, work some hours and some
earn pay, so the work screens bite for both awards. Pay of £8,000 is below
the personal allowance and the primary threshold, and £20,000 is far above
the higher limit for exempt work, so the work reference, which reads
England's income tax rates, decides the same in Scotland and Wales.

Roles are given explicitly (is_claimant_or_partner), so the properties test
the readers rather than role inference. The take-up mode is fixed
(claims_all_entitled_benefits false): that flag sums reports across the
whole simulation, so with it a report anywhere can change would_claim_IS. Each example builds many families in
one simulation, in separate households and benefit units.
"""

import numpy as np
from hypothesis import HealthCheck, event, given, settings
from hypothesis import strategies as st

from legacy_award_work_reference import (
    esa_claimant_in_remunerative_work,
    esa_screen,
    jsa_screen,
    weekly_hours,
)
from policyengine_uk import Simulation

YEAR = 2025
# Merton's working-age council tax reduction scheme has parameters from
# April 2026, so the non-dependant property runs in 2027 (income-related ESA
# only: Income Support and income-based JSA closed in April 2026).
NON_DEP_YEAR = 2027

FAMILY_READERS = [
    "claimant_or_partner_esa_income",
    "claimant_or_partner_jsa_income",
    "housing_benefit_applicable_income",
    "in_receipt_of_income_support_jsa_ib_or_esa_ir",
    "housing_benefit_on_passporting_benefit",
    "housing_benefit_applicable_income_disregard",
    "housing_benefit_assessable_capital",
    "council_tax_reduction_applicable_income",
    "council_tax_reduction_relevant_income_based_benefit",
    "tax_credits_applicable_income",
    "targeted_childcare_entitlement_eligible",
    "would_claim_IS",
    "income_support_eligible",
]
MEMBER_READERS = [
    "is_scp_eligible",
    "maintenance_loan_entitled_to_benefits",
    "is_on_income_related_esa",
    "is_on_income_based_jsa",
    "is_on_income_support",
]
AWARDS = st.sampled_from([0, 0, 200, 3_000])


@st.composite
def award_reports(draw):
    return {
        "esa_income_reported": draw(AWARDS),
        "jsa_income_reported": draw(AWARDS),
        "income_support_reported": draw(AWARDS),
    }


# 0, 15, 16, 24 and 40 hours a week: either side of JSA's 16 hours for a
# claimant, ESA's 16 for permitted work and 24 for either partner.
HOURS = [0, 0, 780, 832, 1_248, 2_080]


@st.composite
def work(draw):
    return {
        "employment_income": draw(st.sampled_from([0, 0, 8_000, 20_000])),
        "hours_worked": draw(st.sampled_from(HOURS)),
    }


@st.composite
def families(draw):
    """A claimant, an optional partner, up to two dependants and sometimes an
    adult outside the couple who is already a member.

    Qualifying young persons and the existing outside adult may report awards
    of their own, so the properties also cover members who are on an award
    in their own right. The claimant, partner and outside adult may work.
    """
    dependants = []
    for _ in range(draw(st.integers(0, 2))):
        if draw(st.booleans()):
            dependants.append({"age": draw(st.integers(0, 15))})
        else:
            # A qualifying young person: 16-19 in non-advanced education.
            dependants.append(
                {
                    "age": draw(st.integers(16, 19)),
                    "current_education": "UPPER_SECONDARY",
                    **draw(award_reports()),
                }
            )
    eldest_dependant = max([d["age"] for d in dependants], default=0)
    adults = []
    for i in range(1 + draw(st.booleans())):
        adults.append(
            {
                "age": draw(st.integers(max(18, eldest_dependant + 16), 60)),
                **draw(work()),
                "is_parent": bool(dependants),
                "receives_carer_benefit": draw(st.booleans()),
                # A disabled claimant or partner gives the family the
                # disability premium, which can put a student partner on the
                # maintenance-loan benefits schedule (HB Regs 2006 reg
                # 56(2)(c)).
                **draw(
                    st.sampled_from(
                        [{}, {"is_disabled_for_benefits": True, "pip_dl": 2_000}]
                    )
                ),
                "care_hours": draw(st.sampled_from([0, 35])),
                "current_education": draw(
                    st.sampled_from(["NOT_IN_EDUCATION", "TERTIARY"])
                ),
                **draw(award_reports()),
            }
        )
    non_couple = list(dependants)
    if draw(st.booleans()):
        non_couple.append(
            {
                "age": draw(st.integers(20, 60)),
                "current_education": "NOT_IN_EDUCATION",
                **draw(work()),
                **draw(award_reports()),
            }
        )
    household = {
        "country": draw(st.sampled_from(["ENGLAND", "SCOTLAND", "WALES"])),
        # £7,000 gives tariff income of £208 a year, more than a £200 report
        # on its own but less than two reports together.
        "savings": draw(st.sampled_from([0, 7_000, 20_000])),
    }
    return adults, non_couple, household


@st.composite
def other_members(draw):
    """An adult who is neither claimant, partner nor a dependant.

    They are under state pension age and not in education, so a 16 to 19 year
    old is not a qualifying young person. They may work, and have no income
    other than their pay and the awards they report.
    """
    return {
        "age": draw(st.integers(16, 60)),
        "current_education": "NOT_IN_EDUCATION",
        **draw(work()),
        **draw(award_reports()),
    }


def situation(units, year=YEAR):
    people, benunits, households = {}, {}, {}
    for i, (adults, non_couple, household, other) in enumerate(units):
        members = [(m, True) for m in adults] + [(m, False) for m in non_couple]
        if other is not None:
            members.append((other, False))
        names = []
        for j, (inputs, claimant_or_partner) in enumerate(members):
            name = f"p{i}_{j}"
            people[name] = {k: {year: v} for k, v in inputs.items()}
            people[name]["is_claimant_or_partner"] = {year: claimant_or_partner}
            names.append(name)
        # claims_all_entitled_benefits sums reports across the whole
        # simulation, so fix the take-up mode per benefit unit: the variants
        # must not share it.
        benunits[f"b{i}"] = {
            "members": names,
            "claims_all_entitled_benefits": {year: False},
        }
        households[f"h{i}"] = {
            "members": names,
            **{k: {year: v} for k, v in household.items()},
        }
    return {"people": people, "benunits": benunits, "households": households}


SETTINGS = settings(
    max_examples=15,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


@SETTINGS
@given(st.lists(st.tuples(families(), other_members()), min_size=1, max_size=6))
def test_other_members_awards_never_change_the_readers(drawn):
    without = [(*family, None) for family, _ in drawn]
    with_other = [(*family, other) for family, other in drawn]
    sim = Simulation(situation=situation(without + with_other))
    flags = sim.calculate("is_claimant_or_partner", YEAR)
    dependant = sim.calculate("is_child_or_young_person_for_legacy_benefits", YEAR)
    sizes = [len(a) + len(d) + (o is not None) for a, d, _, o in without + with_other]
    starts = np.cumsum([0] + sizes[:-1])
    k = len(drawn)
    for i in range(k):
        # The added member is the last of its benefit unit: neither claimant,
        # partner nor a dependant.
        last = starts[k + i] + sizes[k + i] - 1
        assert not flags[last] and not dependant[last], drawn[i]
    for variable in FAMILY_READERS:
        values = sim.calculate(variable, YEAR)
        for i in range(k):
            assert np.isclose(values[i], values[k + i], atol=0.01), (
                variable,
                drawn[i],
            )
    for variable in MEMBER_READERS:
        values = sim.calculate(variable, YEAR)
        for i in range(k):
            n = sizes[i]
            assert np.array_equal(
                values[starts[i] : starts[i] + n],
                values[starts[k + i] : starts[k + i] + n],
            ), (variable, drawn[i])


@SETTINGS
@given(st.lists(st.tuples(families(), other_members()), min_size=1, max_size=6))
def test_claimant_or_partner_awards_bounded_by_benefit_unit_awards(drawn):
    units = [(*family, other) for family, other in drawn]
    sim = Simulation(situation=situation(units))
    for scoped, total, report in [
        ("claimant_or_partner_esa_income", "esa_income", "esa_income_reported"),
        ("claimant_or_partner_jsa_income", "jsa_income", "jsa_income_reported"),
    ]:
        scoped_award = sim.calculate(scoped, YEAR)
        total_award = sim.calculate(total, YEAR)
        assert (scoped_award >= 0).all()
        assert (scoped_award <= total_award + 0.01).all()
        for i, (_, non_couple, _, other) in enumerate(units):
            if other[report] == 0 and all(m.get(report, 0) == 0 for m in non_couple):
                # Nobody outside the couple reports this award: the two
                # coincide.
                assert np.isclose(scoped_award[i], total_award[i]), (scoped, units[i])


def reference_award(reported, capital, params):
    """The income-related award on a reported amount, read directly from the
    regulations. Works on scalars or arrays.

    Capital is the household's savings (the only capital input here), all of
    it the benefit unit's, as it is the only one in its household. Tariff
    income is £1 a week for each £250 or part above £6,000, and capital above
    £16,000 removes the award (ESA Regs 2008 regs 110 and 118; JSA Regs 1996
    regs 107 and 116, as parameterised).
    """
    capital_rules = params.capital
    steps = np.ceil(
        np.maximum(0, capital - capital_rules.tariff_income.threshold)
        / capital_rules.tariff_income.step
    )
    tariff = steps * capital_rules.tariff_income.amount * 52
    return np.where(
        (reported > 0) & (capital <= capital_rules.limit),
        np.maximum(0.0, reported - tariff),
        0.0,
    )


def outside_members(non_couple, other):
    """Members of the benefit unit outside the couple, in simulation order."""
    return list(non_couple) + ([other] if other is not None else [])


def reference_claimant_or_partner_award(
    adults, non_couple, household, other, report, screen, params, parameters
):
    """The award on the claimant's and partner's reports, while the benefit
    unit passes the work screen. When the claimant or partner reports, the
    screen tests only them; otherwise the award on their reports is nil."""
    capital = household["savings"]
    if not screen(adults, outside_members(non_couple, other), capital, parameters):
        return 0.0
    return float(reference_award(sum(a[report] for a in adults), capital, params))


@SETTINGS
@given(st.lists(st.tuples(families(), other_members()), min_size=1, max_size=6))
def test_claimant_or_partner_awards_match_reference(drawn):
    units = [(*family, other) for family, other in drawn]
    sim = Simulation(situation=situation(units))
    parameters = sim.tax_benefit_system.parameters(YEAR)
    dwp = parameters.gov.dwp
    for variable, report, screen, params, active in [
        (
            "claimant_or_partner_esa_income",
            "esa_income_reported",
            esa_screen,
            dwp.ESA.income,
            1,
        ),
        (
            "claimant_or_partner_jsa_income",
            "jsa_income_reported",
            jsa_screen,
            dwp.JSA.income,
            dwp.JSA.income.active,
        ),
    ]:
        award = sim.calculate(variable, YEAR)
        for i, (adults, non_couple, household, other) in enumerate(units):
            expected = active * reference_claimant_or_partner_award(
                adults, non_couple, household, other, report, screen, params, parameters
            )
            if expected == 0 and sum(a[report] for a in adults) > 0:
                event(f"{variable}: a reported award is screened out")
            assert np.isclose(award[i], expected), (variable, units[i])


def payee(sim, claimant_or_partner, reports):
    """The claimant or partner who reports the award, or the claimant (the
    head, else the eldest of the couple) where neither does."""
    benunit = sim.calculate("benunit_id", YEAR, map_to="person")
    head = sim.calculate("is_benunit_head", YEAR) & claimant_or_partner
    age = sim.calculate("age", YEAR)
    result = np.zeros(len(benunit), dtype=bool)
    for unit in np.unique(benunit):
        members = benunit == unit
        couple = members & claimant_or_partner
        reporting = couple & reports
        if reporting.any():
            result |= reporting
        elif (members & head).any():
            result |= members & head
        elif couple.any():
            eldest = np.flatnonzero(couple)[np.argmax(age[couple])]
            result[eldest] = True
    return result


def esa_claimant_works(member, parameters):
    """ESA Regs 2008 reg 41(1) and reg 45: engaged in remunerative work as the
    claimant of their own claim."""
    return esa_claimant_in_remunerative_work(member, parameters)


def jsa_claimant_works(member, parameters):
    """Jobseekers Act 1995 s.1(2)(e), JSA Regs 1996 reg 51(1)(a): 16 hours a
    week or more as the claimant of their own claim."""
    return (
        weekly_hours(member) >= parameters.gov.dwp.JSA.remunerative_work.claimant_hours
    )


@SETTINGS
@given(st.lists(st.tuples(families(), other_members()), min_size=1, max_size=6))
def test_person_is_on_award_from_couple_or_own_report(drawn):
    units = [(*family, other) for family, other in drawn]
    sim = Simulation(situation=situation(units))
    claimant_or_partner = sim.calculate("is_claimant_or_partner", YEAR)
    capital = sim.calculate("savings", YEAR, map_to="person")
    parameters = sim.tax_benefit_system.parameters(YEAR)
    dwp = parameters.gov.dwp
    # Everyone's inputs, in simulation order: the couple, then the members
    # outside it.
    members = [
        member
        for adults, non_couple, _, other in units
        for member in adults + outside_members(non_couple, other)
    ]
    for person_variable, couple_award, report, params, active, works in [
        (
            "is_on_income_related_esa",
            "claimant_or_partner_esa_income",
            "esa_income_reported",
            dwp.ESA.income,
            True,
            esa_claimant_works,
        ),
        (
            "is_on_income_based_jsa",
            "claimant_or_partner_jsa_income",
            "jsa_income_reported",
            dwp.JSA.income,
            dwp.JSA.income.active,
            jsa_claimant_works,
        ),
        (
            "is_on_income_support",
            "income_support",
            "income_support_reported",
            None,
            dwp.income_support.active,
            None,
        ),
    ]:
        on = sim.calculate(person_variable, YEAR)
        reported = sim.calculate(report, YEAR)
        # Of the claimant and partner, only the payee is on a couple's award:
        # the one who reports it, or the claimant where neither does
        # (HB Regs 2006 reg 2(3), (3A): "payable to him").
        couple = (sim.calculate(couple_award, YEAR, map_to="person") > 0) & payee(
            sim, claimant_or_partner, reported > 0
        )
        if params is None:
            # Income Support: their own report, while it is in payment.
            own = active & (reported > 0)
        else:
            # Their own claim: the award on their own report alone, on the
            # household's capital, while they are not in remunerative work
            # as its claimant. Nobody else's report or work matters.
            free = np.array(
                [
                    member.get(report, 0) == 0 or not works(member, parameters)
                    for member in members
                ]
            )
            own = active & free & (reference_award(reported, capital, params) > 0)
            if (~claimant_or_partner & (reported > 0) & ~free).any():
                event(f"{person_variable}: an outside member's work bars them")
        expected = np.where(claimant_or_partner, couple, own)
        assert np.array_equal(on, expected), (person_variable, units)


@settings(
    max_examples=10,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
@given(
    st.lists(
        st.tuples(
            st.lists(st.sampled_from([0, 0, 200, 3_000]), min_size=1, max_size=2),
            st.sampled_from([None, 0, 200, 3_000]),
            st.sampled_from([0, 3_000]),
            st.sampled_from([0, 7_000]),
        ),
        min_size=1,
        max_size=6,
    )
)
def test_other_members_esa_never_changes_non_dependant_exemption(drawn):
    """A non-dependant is exempt only through their own (or couple's) award.

    Each household in Merton has an older applicant (the household head) and a
    non-dependant benefit unit of one or two claimants, sometimes with an adult
    outside their couple who is already a member, with or without a further
    adult who reports income-related ESA. Savings of £7,000 give tariff income
    of £208 a year, more than a £200 report on its own. The existing members'
    individual deductions never change when the further adult is added.
    """
    year = NON_DEP_YEAR
    people, benunits, households = {}, {}, {}
    layouts = []
    for variant, other_present in [(0, False), (1, True)]:
        for i, (claimant_awards, existing_award, other_award, savings) in enumerate(
            drawn
        ):
            tag = f"{variant}_{i}"
            names = [f"applicant_{tag}"]
            people[names[0]] = {"age": {year: 60}}
            unit = []
            for j, award in enumerate(claimant_awards):
                name = f"nondep_{tag}_{j}"
                people[name] = {
                    "age": {year: 30 + j},
                    "is_claimant_or_partner": {year: True},
                    "current_education": {year: "NOT_IN_EDUCATION"},
                    "esa_income_reported": {year: award},
                }
                unit.append(name)
            if existing_award is not None:
                name = f"existing_{tag}"
                people[name] = {
                    "age": {year: 45},
                    "is_claimant_or_partner": {year: False},
                    "current_education": {year: "NOT_IN_EDUCATION"},
                    "esa_income_reported": {year: existing_award},
                }
                unit.append(name)
            if other_present:
                name = f"other_{tag}"
                people[name] = {
                    "age": {year: 25},
                    "is_claimant_or_partner": {year: False},
                    "current_education": {year: "NOT_IN_EDUCATION"},
                    "esa_income_reported": {year: other_award},
                }
                unit.append(name)
            people[names[0]]["is_claimant_or_partner"] = {year: True}
            benunits[f"applicant_unit_{tag}"] = {"members": names}
            benunits[f"nondep_unit_{tag}"] = {
                "members": unit,
                "universal_credit": {year: 0},
            }
            households[f"h_{tag}"] = {
                "members": names + unit,
                "country": {year: "ENGLAND"},
                "local_authority": {year: "MERTON"},
                "savings": {year: savings},
            }
            layouts.append(names + unit)
    sim = Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )
    deduction = dict(
        zip(
            people,
            sim.calculate(
                "merton_council_tax_reduction_individual_non_dep_deduction", year
            ),
        )
    )
    for i in range(len(drawn)):
        without, with_other = layouts[i], layouts[len(drawn) + i]
        for a, b in zip(without, with_other):
            assert np.isclose(deduction[a], deduction[b]), drawn[i]


def _difference(variable, base_people, award_people, benunit_inputs=None):
    def build(people):
        names = list(people)
        return {
            "people": {
                n: {k: {YEAR: v} for k, v in inputs.items()}
                for n, inputs in people.items()
            },
            "benunits": {
                "b": {
                    "members": names,
                    **{k: {YEAR: v} for k, v in (benunit_inputs or {}).items()},
                }
            },
            "households": {"h": {"members": names}},
        }

    base = Simulation(situation=build(base_people)).calculate(variable, YEAR)[0]
    award = Simulation(situation=build(award_people)).calculate(variable, YEAR)[0]
    return award - base


CLAIMANT = {"age": 40, "is_claimant_or_partner": True, "employment_income": 10_000}
OTHER = {
    "age": 30,
    "is_claimant_or_partner": False,
    "current_education": "NOT_IN_EDUCATION",
}


def test_claimant_and_partner_awards_count_in_full_as_their_ctr_income():
    """CTR (Prescribed Requirements) (England) Regs 2012 Sch 1 para 11: the
    partner's income is the applicant's.

    The claimant earns £10,000, below the tax and NI thresholds, so each
    award adds exactly its amount.
    """
    ctr = "council_tax_reduction_applicable_income"
    no_uc = {"universal_credit": 0}
    claimant_esa = {"claimant": {**CLAIMANT, "esa_income_reported": 5_000}}
    assert np.isclose(
        _difference(ctr, {"claimant": CLAIMANT}, claimant_esa, no_uc), 5_000
    )
    partner = {"age": 38, "is_claimant_or_partner": True}
    couple = {"claimant": CLAIMANT, "partner": partner}
    couple_jsa = {
        "claimant": CLAIMANT,
        "partner": {**partner, "jsa_income_reported": 3_000},
    }
    assert np.isclose(_difference(ctr, couple, couple_jsa, no_uc), 3_000)
    # Another member's award adds nothing.
    other_esa = {
        "claimant": CLAIMANT,
        "other": {**OTHER, "esa_income_reported": 5_000},
    }
    with_other = {"claimant": CLAIMANT, "other": OTHER}
    assert np.isclose(_difference(ctr, with_other, other_esa, no_uc), 0)


def _value(variable, people):
    # Not claiming Universal Credit, so the Universal Credit limb of the
    # Housing Benefit passport cannot apply: only the legacy awards can.
    names = list(people)
    situation = {
        "people": {
            n: {k: {YEAR: v} for k, v in inputs.items()} for n, inputs in people.items()
        },
        "benunits": {"b": {"members": names, "would_claim_uc": {YEAR: False}}},
        "households": {"h": {"members": names}},
    }
    return Simulation(situation=situation).calculate(variable, YEAR)[0]


def test_claimant_and_partner_awards_passport_housing_benefit_income():
    """HB Regs 2006 Sch 5 para 4: the whole income of a claimant on
    income-related ESA or income-based JSA is disregarded. The partner's
    award is the couple's (reg 25(1)), so it passports them too, and another
    member's award passports nobody.

    The claimant earns £10,000, below the tax and NI thresholds. Without an
    award their income is assessed, less the £5 a week single or £10 a week
    couple disregard (Sch 4 paras 10 and 7): 10,000 - 260 = 9,740 and
    10,000 - 520 = 9,480.
    """
    hb = "housing_benefit_applicable_income"
    assert np.isclose(_value(hb, {"claimant": CLAIMANT}), 9_740)
    claimant_esa = {"claimant": {**CLAIMANT, "esa_income_reported": 5_000}}
    assert np.isclose(_value(hb, claimant_esa), 0)
    partner = {"age": 38, "is_claimant_or_partner": True}
    assert np.isclose(_value(hb, {"claimant": CLAIMANT, "partner": partner}), 9_480)
    couple_jsa = {
        "claimant": CLAIMANT,
        "partner": {**partner, "jsa_income_reported": 3_000},
    }
    assert np.isclose(_value(hb, couple_jsa), 0)
    # Another member's award: the claimant's income is assessed as before.
    with_other = {"claimant": CLAIMANT, "other": OTHER}
    other_esa = {
        "claimant": CLAIMANT,
        "other": {**OTHER, "esa_income_reported": 5_000},
    }
    assert np.isclose(_value(hb, with_other), 9_740)
    assert np.isclose(_value(hb, other_esa), 9_740)


def _claimant_and_other(other_report):
    people = {
        "claimant": {"age": {YEAR: 40}, "is_claimant_or_partner": {YEAR: True}},
        "other": {
            "age": {YEAR: 30},
            "is_claimant_or_partner": {YEAR: False},
            "current_education": {YEAR: "NOT_IN_EDUCATION"},
            **{k: {YEAR: v} for k, v in other_report.items()},
        },
    }
    return {
        "people": people,
        "benunits": {"b": {"members": list(people)}},
        "households": {"h": {"members": list(people)}},
    }


def test_award_set_after_construction_is_taken_as_entered():
    """An award set with set_input after the simulation is built is entered
    directly, so it is the claimant's whatever another member reports."""
    for variable, scoped, report in [
        ("esa_income", "claimant_or_partner_esa_income", "esa_income_reported"),
        ("jsa_income", "claimant_or_partner_jsa_income", "jsa_income_reported"),
    ]:
        sim = Simulation(situation=_claimant_and_other({report: 5_000}))
        sim.set_input(variable, YEAR, np.array([3_000.0]))
        assert np.isclose(sim.calculate(scoped, YEAR)[0], 3_000), variable


def test_award_set_on_a_branch_is_taken_as_entered_on_that_branch():
    for variable, scoped, report in [
        ("esa_income", "claimant_or_partner_esa_income", "esa_income_reported"),
        ("jsa_income", "claimant_or_partner_jsa_income", "jsa_income_reported"),
    ]:
        sim = Simulation(situation=_claimant_and_other({report: 5_000}))
        branch = sim.get_branch("entered")
        branch.set_input(variable, YEAR, np.array([3_000.0]))
        assert np.isclose(branch.calculate(scoped, YEAR)[0], 3_000), variable
        # The main simulation still reads the reports: another member's award
        # is not the claimant's.
        assert np.isclose(sim.calculate(scoped, YEAR)[0], 0), variable


def test_award_set_after_the_value_is_cached_is_taken_as_entered():
    for variable, scoped, report in [
        ("esa_income", "claimant_or_partner_esa_income", "esa_income_reported"),
        ("jsa_income", "claimant_or_partner_jsa_income", "jsa_income_reported"),
    ]:
        sim = Simulation(situation=_claimant_and_other({report: 5_000}))
        assert np.isclose(sim.calculate(scoped, YEAR)[0], 0), variable
        sim.set_input(variable, YEAR, np.array([3_000.0]))
        sim.delete_arrays(scoped)
        assert np.isclose(sim.calculate(scoped, YEAR)[0], 3_000), variable


def test_late_zero_entry_overrides_the_claimants_reports():
    for variable, scoped, report in [
        ("esa_income", "claimant_or_partner_esa_income", "esa_income_reported"),
        ("jsa_income", "claimant_or_partner_jsa_income", "jsa_income_reported"),
    ]:
        situation = _claimant_and_other({})
        situation["people"]["claimant"][report] = {YEAR: 3_000}
        sim = Simulation(situation=situation)
        sim.set_input(variable, YEAR, np.array([0.0]))
        assert np.isclose(sim.calculate(scoped, YEAR)[0], 0), variable


def _situation(people, year=YEAR):
    names = list(people)
    return {
        "people": {
            n: {k: {year: v} for k, v in inputs.items()} for n, inputs in people.items()
        },
        "benunits": {"b": {"members": names}},
        "households": {"h": {"members": names}},
    }


FULL_TIME_PAY = {"employment_income": 20_000, "hours_worked": 2_080}


def test_a_working_claimants_reported_awards_are_screened_out():
    """WRA 2007 Sch 1 para 6(1)(e); Jobseekers Act 1995 s.1(2)(e).

    A claimant earning £20,000 for 40 hours a week has ESA earnings of about
    £344.61 a week after PAYE (£1,486) and Class 1 (about £594.40), above the
    £195.50 higher limit for exempt work in 2025-26, and works 16 hours or
    more for JSA. Their reported awards are not paid, so the claimant-or-
    partner awards that the readers use are nil, whichever Hypothesis
    examples the properties draw."""
    claimant = {"age": 40, "is_claimant_or_partner": True}
    reports = {"esa_income_reported": 3_000, "jsa_income_reported": 3_000}
    idle = Simulation(situation=_situation({"c": {**claimant, **reports}}))
    working = Simulation(
        situation=_situation({"c": {**claimant, **reports, **FULL_TIME_PAY}})
    )
    for variable in [
        "claimant_or_partner_esa_income",
        "claimant_or_partner_jsa_income",
    ]:
        assert np.isclose(idle.calculate(variable, YEAR)[0], 3_000), variable
        assert working.calculate(variable, YEAR)[0] == 0, variable
    for variable in ["is_on_income_related_esa", "is_on_income_based_jsa"]:
        assert idle.calculate(variable, YEAR)[0], variable
        assert not working.calculate(variable, YEAR)[0], variable


def _claimant_and_outside_adult(claimant_report, claimant_works, other_works):
    claimant = {"age": 40, "is_claimant_or_partner": True}
    other = {
        "age": 30,
        "is_claimant_or_partner": False,
        "current_education": "NOT_IN_EDUCATION",
        "esa_income_reported": 3_000,
        "jsa_income_reported": 3_000,
    }
    for person, works in [(claimant, claimant_works), (other, other_works)]:
        if works:
            person.update(FULL_TIME_PAY)
    claimant["esa_income_reported"] = claimant_report
    claimant["jsa_income_reported"] = claimant_report
    return Simulation(situation=_situation({"c": claimant, "o": other}))


def test_an_outside_adults_own_claim_is_screened_on_their_own_work():
    """An adult outside the couple claims in their own right, so their claim
    is tested on their own work and never on the claimant's (WRA 2007 Sch 1
    para 6(1)(e); Jobseekers Act 1995 s.1(2)(e)). The benefit unit's screen
    tests only the claimant when the claimant reports an award, so it cannot
    stand in for theirs.

    Working full time, they are never on either award, whether or not the
    non-working claimant also reports one. Not working, they stay on both
    when a working claimant's own report fails the screen and leaves the
    benefit unit's award nil."""
    readers = [
        "is_on_income_related_esa",
        "is_on_income_based_jsa",
        "maintenance_loan_entitled_to_benefits",
    ]
    for claimant_report in [0, 3_000]:
        working_other = _claimant_and_outside_adult(
            claimant_report, claimant_works=False, other_works=True
        )
        idle_other = _claimant_and_outside_adult(
            claimant_report, claimant_works=True, other_works=False
        )
        for variable in readers:
            assert not working_other.calculate(variable, YEAR)[1], (
                variable,
                claimant_report,
            )
            assert idle_other.calculate(variable, YEAR)[1], (variable, claimant_report)
    # The working claimant's report fails the screen: the benefit unit's
    # award is nil, and the claimant is on neither award.
    idle_other = _claimant_and_outside_adult(
        3_000, claimant_works=True, other_works=False
    )
    assert idle_other.calculate("esa_income", YEAR)[0] == 0
    assert not idle_other.calculate("is_on_income_related_esa", YEAR)[0]


def test_an_outside_adults_work_keeps_their_non_dependant_deduction():
    """Merton's working-age scheme, as modelled from 2027, takes no
    non-dependant deduction for a non-dependant on income-related ESA, read
    from is_on_income_related_esa (the common council tax reduction helper).

    In a non-dependant benefit unit of a claimant and an adult outside their
    couple, the outside adult's own ESA report exempts them only when their
    own claim passes: working full time, their deduction is the same as if
    they reported nothing, whatever the claimant reports; not working, they
    are exempt whatever the working claimant reports."""
    year = NON_DEP_YEAR

    def deduction(claimant_report, other_report, claimant_works, other_works):
        def member(age, role, report, works):
            inputs = {
                "age": {year: age},
                "is_claimant_or_partner": {year: role},
                "current_education": {year: "NOT_IN_EDUCATION"},
                "esa_income_reported": {year: report},
            }
            if works:
                inputs.update({k: {year: v} for k, v in FULL_TIME_PAY.items()})
            return inputs

        people = {
            "applicant": {"age": {year: 50}, "is_claimant_or_partner": {year: True}},
            "claimant": member(40, True, claimant_report, claimant_works),
            "other": member(30, False, other_report, other_works),
        }
        sim = Simulation(
            situation={
                "people": people,
                "benunits": {
                    "applicant_unit": {"members": ["applicant"]},
                    "non_dependant_unit": {
                        "members": ["claimant", "other"],
                        "universal_credit": {year: 0},
                    },
                },
                "households": {
                    "h": {
                        "members": list(people),
                        "country": {year: "ENGLAND"},
                        "local_authority": {year: "MERTON"},
                        "savings": {year: 0},
                    }
                },
            }
        )
        return sim.calculate(
            "merton_council_tax_reduction_individual_non_dep_deduction", year
        )[2]

    not_on_esa = deduction(0, 0, claimant_works=False, other_works=True)
    assert not_on_esa > 0
    for claimant_report in [0, 3_000]:
        assert np.isclose(
            deduction(claimant_report, 3_000, claimant_works=False, other_works=True),
            not_on_esa,
        ), claimant_report
        assert (
            deduction(claimant_report, 3_000, claimant_works=True, other_works=False)
            == 0
        ), claimant_report
