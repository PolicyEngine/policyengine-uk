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
- Which Housing Benefit regulations apply to a pensioner: HB Regs 2006 reg
  5(1)(b); SI 2006/214 reg 5(2). The mixed-age couple Pension Credit saving:
  SI 2019/37 arts 2(3) and 4, through SI 2006/214 reg 5.
- The extended childcare parent and partner conditions: SI 2022/1134 regs
  11A(1)(e), 14(4)(b) and 15(4).

A member of the benefit unit who is neither the claimant, the partner nor a
child or young person they are responsible for (for example a non-dependent
adult) claims in their own right, so:

- adding such a member, whatever Income Support, income-based JSA or
  income-related ESA they report, never changes any of these readers for the
  claimant's family or for its existing members;
- the claimant-or-partner awards are bounded by the benefit-unit awards
  (0 <= claimant_or_partner_esa_income <= esa_income, likewise for JSA) and
  equal them when no other member reports an award;
- a person is on an award exactly when they are the payee of their couple's
  positive award (the claimant or partner who reports it, or the claimant)
  or, for anyone else, when the award on their own report alone is positive
  after tariff income from the household's capital and within the capital
  limit (Income Support: when they report it).

Roles are given explicitly (is_claimant_or_partner), so the properties test
the readers rather than role inference. The take-up mode is fixed
(claims_all_entitled_benefits false): that flag sums reports across the
whole simulation, so with it a report anywhere can change would_claim_IS. Each example builds many families in
one simulation, in separate households and benefit units.
"""

import numpy as np
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

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
    "housing_benefit_pension_age_regulations_apply",
    "has_mixed_age_couple_pension_credit_saving",
]
MEMBER_READERS = [
    "is_scp_eligible",
    "maintenance_loan_entitled_to_benefits",
    "is_on_income_related_esa",
    "is_on_income_based_jsa",
    "is_on_income_support",
    "extended_childcare_entitlement_limited_capability_or_specified_benefit",
]
AWARDS = st.sampled_from([0, 0, 200, 3_000])


@st.composite
def award_reports(draw):
    return {
        "esa_income_reported": draw(AWARDS),
        "jsa_income_reported": draw(AWARDS),
        "income_support_reported": draw(AWARDS),
    }


@st.composite
def families(draw):
    """A claimant, an optional partner, up to two dependants and sometimes an
    adult outside the couple who is already a member.

    Qualifying young persons and the existing outside adult may report awards
    of their own, so the properties also cover members who are on an award
    in their own right.
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
                "employment_income": draw(st.sampled_from([0, 0, 8_000, 20_000])),
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
    old is not a qualifying young person. They have no income other than the
    awards they report.
    """
    return {
        "age": draw(st.integers(16, 60)),
        "current_education": "NOT_IN_EDUCATION",
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


# --- Further family shapes (begin) ---
# Some readers only bite for a claimant over state pension age (the Housing
# Benefit regulations that apply, the mixed-age couple saving), for a single
# applicant under 25, or for parents of a young child of whom only one works
# (the extended childcare partner condition). The families above rarely take
# those shapes, so three more properties check every family and member reader
# on them. The claimant and partner seldom report an award themselves, and the
# added member's award survives tariff income on the savings drawn, so a
# reader that wrongly counts it changes. The invariant is about the readers'
# own scoping: the shapes pay no rent, so Universal Credit stays far below the
# benefit cap. The cap still counts every member's award (benefit_cap_reduction
# reads the benefit-unit totals), so with a binding cap another member's award
# can reach a reader through Universal Credit.
PENSION_AGE = 68
# Whether the pension-age property enters is_mixed_age_couple, so that a
# reader of the couple's award reports is tested on those reports alone.
ENTER_IS_MIXED_AGE_COUPLE = True
AWARD_REPORTS = [
    "esa_income_reported",
    "jsa_income_reported",
    "income_support_reported",
]


@st.composite
def couple_award_reports(draw):
    """Usually no award; otherwise £3,000 of one of them."""
    reports = dict.fromkeys(AWARD_REPORTS, 0)
    award = draw(st.sampled_from([None] * 4 + AWARD_REPORTS))
    if award is not None:
        reports[award] = 3_000
    return reports


@st.composite
def other_members_with_awards(draw):
    """As other_members, with at least one award of £3,000 or more."""
    awards = {
        "esa_income_reported": draw(st.sampled_from([0, 3_000, 5_000])),
        "jsa_income_reported": draw(st.sampled_from([0, 3_000, 5_000])),
        "income_support_reported": draw(st.sampled_from([0, 3_000, 5_000])),
    }
    if not any(awards.values()):
        awards[draw(st.sampled_from(sorted(awards)))] = 5_000
    return {
        "age": draw(st.integers(16, 60)),
        "current_education": "NOT_IN_EDUCATION",
        **awards,
    }


@st.composite
def pension_age_families(draw):
    """A claimant over state pension age, usually with a partner of working or
    pension age (so many couples are mixed-age), and no dependants. Ages are
    listed rather than ranged so that both sides of the 14 May 2019 cut-off
    for the mixed-age couple saving (born by 1954) are drawn."""
    ages = [
        draw(st.sampled_from([PENSION_AGE, 72, 76, 81])),
        draw(st.sampled_from([45, 58, 63, 70, 79])),
    ]
    adults = []
    for age in ages[: 1 + draw(st.sampled_from([0, 1, 1]))]:
        adults.append(
            {
                "age": age,
                "employment_income": draw(st.sampled_from([0, 3_000, 12_000])),
                "housing_benefit_reported": draw(st.sampled_from([0, 3_000, 3_000])),
                **draw(couple_award_reports()),
            }
        )
    household = {
        "country": draw(st.sampled_from(["ENGLAND", "SCOTLAND", "WALES"])),
        "savings": draw(st.sampled_from([0, 7_000, 20_000])),
    }
    return adults, [], household


@st.composite
def young_single_families(draw):
    """A single applicant aged 18 to 24 in Scotland or Wales, no dependants."""
    adults = [
        {
            "age": draw(st.integers(18, 24)),
            "employment_income": draw(st.sampled_from([0, 3_000, 12_000])),
            "current_education": "NOT_IN_EDUCATION",
            **draw(couple_award_reports()),
        }
    ]
    household = {
        "country": draw(st.sampled_from(["SCOTLAND", "WALES"])),
        "savings": draw(st.sampled_from([0, 7_000])),
    }
    return adults, [], household


@st.composite
def working_parent_families(draw):
    """Parents of a child aged one to four in England. One parent is in
    qualifying paid work within the income limits and the other is not, so
    the other meets the extended childcare partner condition only through
    limited capability for work or a specified benefit (SI 2022/1134 regs
    14(4) and 15(4))."""
    working = {
        "age": draw(st.integers(25, 45)),
        "is_parent": True,
        "in_work": True,
        "employment_income": draw(st.sampled_from([20_000, 30_000])),
        "extended_childcare_entitlement_meets_income_requirements": True,
        **draw(couple_award_reports()),
    }
    not_working = {
        "age": draw(st.integers(25, 45)),
        "is_parent": True,
        "in_work": False,
        "extended_childcare_entitlement_meets_income_requirements": False,
        **draw(couple_award_reports()),
    }
    household = {
        "country": "ENGLAND",
        "savings": draw(st.sampled_from([0, 7_000, 20_000])),
    }
    return [working, not_working], [{"age": draw(st.integers(1, 4))}], household


def _family_readers_never_change(drawn, enter_is_mixed_age_couple=False):
    without = [(*family, None) for family, _ in drawn]
    with_other = [(*family, other) for family, other in drawn]
    units = without + with_other
    inputs = situation(units)
    if enter_is_mixed_age_couple:
        for i, (adults, _, _, _) in enumerate(units):
            pension_age = [a["age"] >= PENSION_AGE for a in adults]
            inputs["benunits"][f"b{i}"]["is_mixed_age_couple"] = {
                YEAR: len(adults) == 2 and sum(pension_age) == 1
            }
    sim = Simulation(situation=inputs)
    flags = sim.calculate("is_claimant_or_partner", YEAR)
    sizes = [len(a) + len(d) + (o is not None) for a, d, _, o in units]
    starts = np.cumsum([0] + sizes[:-1])
    k = len(drawn)
    for i in range(k):
        assert not flags[starts[k + i] + sizes[k + i] - 1], drawn[i]
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
@given(
    st.lists(
        st.tuples(pension_age_families(), other_members_with_awards()),
        min_size=1,
        max_size=6,
    )
)
def test_other_members_awards_never_change_the_readers_at_pension_age(drawn):
    _family_readers_never_change(drawn, ENTER_IS_MIXED_AGE_COUPLE)


@SETTINGS
@given(
    st.lists(
        st.tuples(young_single_families(), other_members_with_awards()),
        min_size=1,
        max_size=6,
    )
)
def test_other_members_awards_never_change_the_readers_for_young_singles(drawn):
    _family_readers_never_change(drawn)


@SETTINGS
@given(
    st.lists(
        st.tuples(working_parent_families(), other_members_with_awards()),
        min_size=1,
        max_size=6,
    )
)
def test_other_members_awards_never_change_the_readers_for_working_parents(drawn):
    _family_readers_never_change(drawn)


# --- Further family shapes (end) ---


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


def reference_claimant_or_partner_award(adults, household, report, params):
    """The award on the claimant's and partner's reports."""
    return float(
        reference_award(sum(a[report] for a in adults), household["savings"], params)
    )


@SETTINGS
@given(st.lists(st.tuples(families(), other_members()), min_size=1, max_size=6))
def test_claimant_or_partner_awards_match_reference(drawn):
    units = [(*family, other) for family, other in drawn]
    sim = Simulation(situation=situation(units))
    dwp = sim.tax_benefit_system.parameters(YEAR).gov.dwp
    for variable, report, params, active in [
        ("claimant_or_partner_esa_income", "esa_income_reported", dwp.ESA.income, 1),
        (
            "claimant_or_partner_jsa_income",
            "jsa_income_reported",
            dwp.JSA.income,
            dwp.JSA.income.active,
        ),
    ]:
        award = sim.calculate(variable, YEAR)
        for i, (adults, _, household, other) in enumerate(units):
            expected = active * reference_claimant_or_partner_award(
                adults, household, report, params
            )
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


@SETTINGS
@given(st.lists(st.tuples(families(), other_members()), min_size=1, max_size=6))
def test_person_is_on_award_from_couple_or_own_report(drawn):
    units = [(*family, other) for family, other in drawn]
    sim = Simulation(situation=situation(units))
    claimant_or_partner = sim.calculate("is_claimant_or_partner", YEAR)
    capital = sim.calculate("savings", YEAR, map_to="person")
    dwp = sim.tax_benefit_system.parameters(YEAR).gov.dwp
    for person_variable, couple_award, report, params, active in [
        (
            "is_on_income_related_esa",
            "claimant_or_partner_esa_income",
            "esa_income_reported",
            dwp.ESA.income,
            True,
        ),
        (
            "is_on_income_based_jsa",
            "claimant_or_partner_jsa_income",
            "jsa_income_reported",
            dwp.JSA.income,
            dwp.JSA.income.active,
        ),
        (
            "is_on_income_support",
            "income_support",
            "income_support_reported",
            None,
            dwp.income_support.active,
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
            # The award on their own report alone, on the household's capital.
            own = active & (reference_award(reported, capital, params) > 0)
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
