"""Income Support reads the current claimant/partner award value convention.

The helper switch once matched literal historical inline readers. Separate
outside-claim screening intentionally changes that aggregate formula, so
this file now checks an independent CURRENT per-claim reference. Work and
capital are read using the existing plain-Python legal reference, with the
original couple and separate outside claims; expected full/scoped amounts
never call production award callbacks. Stored float32/half-penny, plain-total,
arbitrary input, zero and explicit scoped-input conventions are retained.
A plain total can differ from a screened-reports reading; that comparison
is a declared counterfactual value convention, not historical-code equality.
"""

import numpy as np
import pytest
from hypothesis import event, given
from hypothesis import strategies as st
from policyengine_core.periods import period as as_period

from policyengine_uk import Simulation
from policyengine_uk.model_api import add
from policyengine_uk.tests import legacy_award_work_reference as reference
from policyengine_uk.tests.test_income_support_eligibility_properties import (
    DIFFERENTIAL_SETTINGS,
    FAMILIES,
    input_settings,
    situation as property_situation,
)

YEAR = 2025
HALF_PENNY = 0.005
LIMBS = {
    "esa_income": (
        "esa_income_reported",
        "ESA",
        "claimant_or_partner_esa_income",
    ),
    "jsa_income": (
        "jsa_income_reported",
        "JSA",
        "claimant_or_partner_jsa_income",
    ),
}


def reference_report_awards(benunit, period, award):
    """Independent per-claim full and original-couple amounts on open reports."""
    person = benunit.members
    names = [
        "age",
        "hours_worked",
        "employment_income",
        "self_employment_income",
        "employee_pension_contributions",
        "personal_pension_contributions",
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "statutory_paternity_pay",
        "receives_carer_benefit",
        "care_hours",
        "income_support_reported",
        "pension_credit_reported",
        "esa_income_reported",
        "jsa_income_reported",
        # The ESA reference reads the model's pensionable age (WRA 2007
        # s.1(3)(c)).
        "is_SP_age",
    ]
    arrays = {name: person(name, period) for name in names}
    roles = person("is_claimant_or_partner", period)
    closed_name = (
        "esa_income_report_closed"
        if award == "esa_income"
        else "person_legacy_benefits_closed"
    )
    closed = person(closed_name, period)
    capitals = benunit(f"{award}_assessable_capital", period)
    parameters = benunit.simulation.tax_benefit_system.parameters(period)
    is_esa = award == "esa_income"
    rules = parameters.gov.dwp.ESA.income if is_esa else parameters.gov.dwp.JSA.income
    screen = reference.esa_screen if is_esa else reference.jsa_screen
    # Sch 1 para 6(1)(c) and (d), through the model's proxy for the couple
    # being on State Pension Credit. It never bars an outside member's claim.
    on_pension_credit = benunit("meets_pension_credit_age_conditions", period) & (
        benunit("would_claim_pc", period)
    )

    def passes(members, unit, couple):
        if not is_esa:
            return screen(members, [], capitals[unit], parameters)
        return screen(
            members,
            [],
            capitals[unit],
            parameters,
            on_pension_credit=couple and on_pension_credit[unit],
        )

    full, scoped = [], []
    for unit in range(benunit.count):
        ids = np.flatnonzero(benunit.members_entity_id == unit)
        members = []
        for i in ids:
            member = {name: float(value[i]) for name, value in arrays.items()}
            if closed[i]:
                member[f"{award}_reported"] = 0
            members.append((i, member))
        couple = [member for i, member in members if roles[i]]
        others = [member for i, member in members if not roles[i]]
        capital = capitals[unit]
        tariff = reference.tariff_income(capital, rules.capital)
        active = is_esa or parameters.gov.dwp.JSA.income.active
        couple_amount = (
            max(0, sum(member[f"{award}_reported"] for member in couple) - tariff)
            if active and passes(couple, unit, couple=True)
            else 0
        )
        outside_amount = sum(
            max(0, member[f"{award}_reported"] - tariff)
            for member in others
            if active and passes([member], unit, couple=False)
        )
        full.append(couple_amount + outside_amount)
        scoped.append(couple_amount)
    return np.array(full), np.array(scoped)


def reference_income_support_eligible(benunit, period, parameters):
    IS = parameters(period).gov.dwp.income_support
    person = benunit.members
    claimant_or_partner = person("is_claimant_or_partner", period)
    has_award = claimant_or_partner & (person("income_support_reported", period) > 0)
    youngest_child_5_or_under = (
        benunit("youngest_child_age_for_legacy_benefits", period)
        <= IS.eligibility.lone_parent_youngest_child_age_limit
    )
    lone_parent_with_young_child = (
        benunit("is_lone_parent", period) & youngest_child_5_or_under
    )
    placed_child = (
        person("is_looked_after_by_local_authority", period)
        & person("is_child_for_child_benefit", period)
        & ~claimant_or_partner
    )
    single_with_placed_child = benunit("is_single", period) & benunit.any(placed_child)
    prescribed_category = person("is_carer_for_benefits", period) | benunit.project(
        lone_parent_with_young_child | single_with_placed_child
    )
    under_qualifying_age = ~person(
        "has_attained_state_pension_credit_qualifying_age", period
    )
    WORK = IS.eligibility.remunerative_work
    hours = person("income_support_remunerative_work_hours", period)
    not_treated_as_working = person("is_carer_for_benefits", period)
    works_as_claimant = ~not_treated_as_working & (hours >= WORK.claimant_hours)
    works_as_partner = (
        claimant_or_partner & ~not_treated_as_working & (hours >= WORK.partner_hours)
    )
    other_member_works = (
        benunit.project(benunit.sum(works_as_partner)) - works_as_partner
    ) > 0
    no_contributory_jsa = person("jsa_contrib", period) <= 0
    no_contributory_esa = person("esa_contrib", period) <= 0
    claimant = (
        has_award
        & prescribed_category
        & under_qualifying_age
        & no_contributory_esa
        & no_contributory_jsa
        & ~works_as_claimant
        & ~other_member_works
    )
    income_related_esa = reference_limb(benunit, period, "esa_income")[1]
    income_based_jsa = reference_limb(benunit, period, "jsa_income")[1]
    on_pension_credit = benunit(
        "meets_pension_credit_age_conditions", period
    ) & benunit("would_claim_pc", period)
    capital = benunit("income_support_assessable_capital", period)
    return (
        benunit.any(claimant)
        & ~on_pension_credit
        & ~income_related_esa
        & ~income_based_jsa
        & (capital <= IS.means_test.capital.limit)
    )


def reference_limb(benunit, period, award):
    """Current per-claim reference, plus the screened-raw counterfactual."""
    reported, _, _ = LIMBS[award]
    person = benunit.members
    claimant_or_partner = person("is_claimant_or_partner", period)
    stored = benunit(award, period)
    reported_total = add(benunit, period, [reported])
    on_all_reports, on_claimant_or_partner_reports = reference_report_awards(
        benunit, period, award
    )
    claimant_or_partner_reported = benunit.sum(
        person(reported, period) * claimant_or_partner
    )
    as_formula = np.isclose(
        stored, on_all_reports.astype(stored.dtype), rtol=0, atol=HALF_PENNY
    )
    as_reported_total = np.isclose(
        stored, reported_total.astype(stored.dtype), rtol=0, atol=HALF_PENNY
    )
    limb = (stored > HALF_PENNY) & (
        ~(as_formula | as_reported_total)
        | (on_claimant_or_partner_reports > HALF_PENNY)
    )
    # The intended reading in the plain-total case: the claimant's and
    # partner's reports paid in full.
    plain_total_only = as_reported_total & ~as_formula
    intended = np.where(
        plain_total_only,
        (stored > HALF_PENNY) & (claimant_or_partner_reported > HALF_PENNY),
        limb,
    )
    return limb, intended, plain_total_only


def fresh(simulation, variables):
    for variable in variables:
        simulation.delete_arrays(variable)


def compare(simulation, year=YEAR):
    """Check the current independent contract, never literal old-code equality."""
    period = as_period(year)
    benunit = simulation.populations["benunit"]
    fresh(
        simulation,
        ["income_support_eligible", *[limb[2] for limb in LIMBS.values()]],
    )
    differs = np.zeros(benunit.count, dtype=bool)
    for award, (_, _, variable) in LIMBS.items():
        old, intended, plain_total_only = reference_limb(benunit, period, award)
        new = simulation.calculate(variable, year) > 0
        np.testing.assert_array_equal(new, intended, err_msg=award)
        np.testing.assert_array_equal(
            new[~plain_total_only], old[~plain_total_only], err_msg=award
        )
        differs |= plain_total_only & (new != old)
    old_gate = reference_income_support_eligible(
        benunit, period, simulation.tax_benefit_system.parameters
    )
    new_gate = simulation.calculate("income_support_eligible", year)
    np.testing.assert_array_equal(new_gate, old_gate)
    return differs


CARER = {
    "age": 40,
    "is_claimant_or_partner": True,
    "receives_carer_benefit": True,
    "income_support_reported": 1_000,
}
PARTNER = {"age": 42, "is_claimant_or_partner": True}
OTHER_ADULT = {
    "age": 30,
    "is_claimant_or_partner": False,
    "current_education": "NOT_IN_EDUCATION",
}

# Each family is (members, capital). The carer satisfies every other
# condition, so only the income-related limbs decide eligibility.
EXAMPLES = [
    ([CARER], 0),
    ([CARER, {**OTHER_ADULT, "esa_income_reported": 3_000}], 0),
    ([CARER, {**OTHER_ADULT, "jsa_income_reported": 3_000}], 0),
    ([CARER, {**PARTNER, "esa_income_reported": 3_000}], 0),
    ([CARER, {**PARTNER, "jsa_income_reported": 3_000}], 0),
    # £10,000 of capital: tariff income of £832 a year extinguishes the
    # partner's own £200 on the formula's reading.
    (
        [
            CARER,
            {**PARTNER, "esa_income_reported": 200, "jsa_income_reported": 200},
            {
                **OTHER_ADULT,
                "esa_income_reported": 3_000,
                "jsa_income_reported": 3_000,
            },
        ],
        10_000,
    ),
]
OVER_TARIFF = len(EXAMPLES) - 1


def simulation(families, entered=None):
    people, benunits, households = {}, {}, {}
    for i, (members, capital) in enumerate(families):
        names = []
        for j, inputs in enumerate(members):
            name = f"p{i}_{j}"
            people[name] = {k: {YEAR: v} for k, v in inputs.items()}
            names.append(name)
        # Legacy claimants: a Universal Credit claim would end the couple's
        # income-related ESA (esa_income_report_closed).
        benunits[f"b{i}"] = {
            "members": names,
            "income_support_assessable_capital": {YEAR: capital},
            "esa_income_assessable_capital": {YEAR: capital},
            "jsa_income_assessable_capital": {YEAR: capital},
            "would_claim_uc": {YEAR: False},
        }
        for award, values in (entered or {}).items():
            benunits[f"b{i}"][award] = {YEAR: values[i]}
        households[f"h{i}"] = {"members": names}
    return Simulation(
        situation={"people": people, "benunits": benunits, "households": households}
    )


def gate(simulation):
    fresh(
        simulation,
        ["income_support_eligible", *[limb[2] for limb in LIMBS.values()]],
    )
    return simulation.calculate("income_support_eligible", YEAR).tolist()


ENTERED = [4_000, 0, 4_000, 0, 3_000, 4_000]


def test_formula_mode_agrees():
    sim = simulation(EXAMPLES)
    assert not compare(sim).any()
    # Only the claimant's and partner's own awards bar the claim.
    assert gate(sim) == [True, True, True, False, False, True]


def test_awards_entered_in_the_situation_agree():
    for award in LIMBS:
        assert not compare(simulation(EXAMPLES, {award: ENTERED})).any(), award


def test_awards_set_after_calculating_agree():
    sim = simulation(EXAMPLES)
    compare(sim)
    for award in LIMBS:
        sim.set_input(award, YEAR, np.array(ENTERED, dtype=float))
        assert not compare(sim).any(), award


def test_awards_set_on_a_branch_agree_there_and_leave_the_parent_alone():
    sim = simulation(EXAMPLES)
    before = gate(sim)
    branch = sim.get_branch("entered", clone_system=False)
    for award in LIMBS:
        branch.set_input(award, YEAR, np.array(ENTERED, dtype=float))
    assert not compare(branch).any()
    assert not compare(sim).any()
    assert gate(sim) == before
    nested = branch.get_branch("zero", clone_system=False)
    nested.set_input("esa_income", YEAR, np.zeros(len(EXAMPLES)))
    assert not compare(nested).any()


def test_a_deleted_award_is_recalculated_and_agrees():
    sim = simulation(EXAMPLES)
    before = gate(sim)
    for award in LIMBS:
        sim.set_input(award, YEAR, np.array(ENTERED, dtype=float))
    assert not compare(sim).any()
    for award in LIMBS:
        sim.delete_arrays(award)
    assert not compare(sim).any()
    assert gate(sim) == before


def test_a_plain_total_reads_the_claimant_and_partner_reports_in_full():
    # Intended difference. The stored award is the plain total of everyone's
    # reports. In the last family the partner's £200 is extinguished by
    # tariff income on the formula's reading; the old limb read that, and did
    # not bar the claim. The plain total pays the £200 in full, so it does.
    for award, (reported, _, variable) in LIMBS.items():
        sim = simulation(EXAMPLES)
        plain_total = sim.calculate(reported, YEAR, map_to="benunit")
        sim.set_input(award, YEAR, plain_total)
        differs = compare(sim)
        assert differs.tolist() == [i == OVER_TARIFF for i in range(len(EXAMPLES))]
        assert sim.calculate(variable, YEAR)[OVER_TARIFF] == 200
        old_gate = reference_income_support_eligible(
            sim.populations["benunit"],
            as_period(YEAR),
            sim.tax_benefit_system.parameters,
        )
        assert not old_gate[OVER_TARIFF]
        assert not gate(sim)[OVER_TARIFF]


# Stored values at and around both readings, half a penny either side.
OFFSETS = [0, 0, 0.004, -0.004, 0.006, -0.006]


@st.composite
def stored_award_families(draw):
    """A claimant, an optional partner and an optional adult outside the
    couple, each reporting ESA and JSA, and how each award is stored."""
    amounts = st.sampled_from([0, 0, 0.004, 200, 3_000, 65_536.01])
    members = [
        {**CARER, "esa_income_reported": draw(amounts), "jsa_income_reported": 0}
    ]
    members[0]["jsa_income_reported"] = draw(amounts)
    if draw(st.booleans()):
        members.append(
            {
                **PARTNER,
                "esa_income_reported": draw(amounts),
                "jsa_income_reported": draw(amounts),
            }
        )
    if draw(st.booleans()):
        members.append(
            {
                **OTHER_ADULT,
                "esa_income_reported": draw(amounts),
                "jsa_income_reported": draw(amounts),
            }
        )
    capital = draw(st.sampled_from([0, 6_250, 10_000, 20_000]))
    storage = {
        award: (
            draw(st.sampled_from(["formula", "plain_total", "entered", "zero"])),
            draw(st.sampled_from(OFFSETS)),
        )
        for award in LIMBS
    }
    return (members, capital), storage


@DIFFERENTIAL_SETTINGS
@given(st.lists(stored_award_families(), min_size=1, max_size=10))
def test_the_limbs_read_every_stored_value_as_intended(drawn):
    families = [family for family, _ in drawn]
    sim = simulation(families)
    for award, (reported, _, _) in LIMBS.items():
        formula = sim.calculate(award, YEAR).astype(float)
        plain_total = sim.calculate(reported, YEAR, map_to="benunit")
        stored = []
        for i, (_, storage) in enumerate(drawn):
            mode, offset = storage[award]
            base = {
                "formula": formula[i],
                "plain_total": plain_total[i],
                "entered": 4_000,
                "zero": 0,
            }[mode]
            stored.append(max(0, base + offset))
            event(f"{award} stored as {mode}")
        sim.set_input(award, YEAR, np.array(stored))
    if compare(sim).any():
        event("the plain-total reading changes a family's eligibility")
    # The claimant's and partner's award is never negative and never more
    # than the stored award it is part of (to the half penny of the rule).
    for award, (_, _, variable) in LIMBS.items():
        scoped = sim.calculate(variable, YEAR)
        assert (scoped >= 0).all(), award
        assert (scoped <= sim.calculate(award, YEAR) + 0.005).all(), award


@DIFFERENTIAL_SETTINGS
@given(FAMILIES, st.data())
def test_the_switched_gate_matches_the_replaced_code(drawn, data):
    # The historical selector name is retained; comparison now uses the
    # independent current per-claim contract, not the old scalar total.
    # Families have outside reporters and formula or direct0/4000 awards.
    capital_as_savings, esa_income, jsa_income = data.draw(input_settings(len(drawn)))
    units = [(*family, extra) for family, extra in drawn]
    sim = Simulation(
        situation=property_situation(units, capital_as_savings, esa_income, jsa_income)
    )
    assert not compare(sim).any()


# What the adult outside the couple reports in the entered-award cases. With
# £3,000 of the award stored for the benefit unit, a report of £3,000 is what
# the reports give, so the replaced code read the stored award through them
# and took it to be the outside adult's; £2,000 and £5,000 are not, so it
# took the stored award to be the couple's. Neither reading looked at the
# claimant-or-partner award entered beside it.
OUTSIDE_REPORTS = [2_000, 3_000, 5_000]


def entered_directly(award, scoped):
    """A carer otherwise eligible for Income Support and an adult outside the
    couple who reports each of OUTSIDE_REPORTS of the award, one family each.
    £3,000 of the award is entered for the benefit unit and `scoped` as the
    claimant's and partner's."""
    reported, _, variable = LIMBS[award]
    families = [
        ([CARER, {**OTHER_ADULT, reported: other}], 0) for other in OUTSIDE_REPORTS
    ]
    n = len(families)
    sim = simulation(families, {award: [3_000] * n, variable: [scoped] * n})
    # Income-based JSA closed on 1 April 2026; the cases need a year in which
    # it still pays awards.
    assert sim.tax_benefit_system.parameters(YEAR).gov.dwp.JSA.income.active
    assert sim.calculate(award, YEAR).tolist() == [3_000] * n
    assert sim.calculate(variable, YEAR).tolist() == [scoped] * n
    return sim


@pytest.mark.parametrize("award", LIMBS)
def test_an_entered_claimant_or_partner_award_bars_the_claim(award):
    # The couple are on the income-related award (s.124(1)(h) for ESA, (f)
    # for JSA), so Income Support is barred whatever the outside adult
    # reports. The replaced code let the claim through where that report was
    # £3,000; #2013's gate, which had no JSA limb, let every JSA case through.
    sim = entered_directly(award, 3_000)
    assert sim.calculate("income_support_eligible", YEAR).tolist() == [False] * 3
    assert sim.calculate("income_support", YEAR).tolist() == [0] * 3


@pytest.mark.parametrize("award", LIMBS)
def test_an_entered_zero_claimant_or_partner_award_never_bars_the_claim(award):
    # The £3,000 stored for the benefit unit is all the outside adult's, so it
    # never bars the claim. The replaced code barred it where that adult's
    # report was not £3,000.
    sim = entered_directly(award, 0)
    assert sim.calculate("income_support_eligible", YEAR).tolist() == [True] * 3
    assert (sim.calculate("income_support", YEAR) > 0).all()


@st.composite
def entered_awards(draw, n):
    """What is entered for each of n families. esa_income and jsa_income are
    calculated, or entered for every family as £0, £3,000 (what an outside
    adult's report can give) or £4,000. The claimant-or-partner awards are
    always entered, for every family."""
    entries = {}
    for award, (_, _, variable) in LIMBS.items():
        if draw(st.booleans()):
            entries[award] = draw(
                st.lists(st.sampled_from([0, 3_000, 4_000]), min_size=n, max_size=n)
            )
        entries[variable] = draw(
            st.lists(st.sampled_from([0, 0, 3_000, 4_000]), min_size=n, max_size=n)
        )
    return entries


@DIFFERENTIAL_SETTINGS
@given(FAMILIES, st.data())
def test_an_entered_claimant_or_partner_award_alone_decides_its_limb(drawn, data):
    # Families from the eligibility properties, each with an adult outside
    # the couple, in three copies:
    # - as drawn, with the claimant-or-partner awards entered;
    # - the same, with the outside adult's ESA and JSA reports redrawn;
    # - as drawn, with the claimant-or-partner awards entered as zero.
    # The outside adult's reports never change the gate, and an entered award
    # bars the claim exactly when it is positive (s.124(1)(f), (h)).
    k = len(drawn)
    capital_as_savings = data.draw(st.booleans())
    entries = data.draw(entered_awards(k))
    outside = st.sampled_from([0, 2_000, 3_000, 5_000])
    redrawn = data.draw(st.lists(st.tuples(outside, outside), min_size=k, max_size=k))
    as_drawn = [(*family, extra) for family, extra in drawn]
    moved = [
        (*family, {**extra, "esa_income_reported": esa, "jsa_income_reported": jsa})
        for (family, extra), (esa, jsa) in zip(drawn, redrawn)
    ]
    situation = property_situation(
        as_drawn + moved + as_drawn,
        capital_as_savings,
        entries.get("esa_income"),
        entries.get("jsa_income"),
    )
    variables = [variable for _, _, variable in LIMBS.values()]
    for i in range(3 * k):
        for variable in variables:
            value = entries[variable][i % k] if i < 2 * k else 0
            situation["benunits"][f"b{i}"][variable] = {YEAR: value}
    sim = Simulation(situation=situation)
    for variable in variables:
        expected = entries[variable] * 2 + [0] * k
        assert sim.calculate(variable, YEAR).tolist() == expected, variable
    eligible = sim.calculate("income_support_eligible", YEAR)
    entered, redrawn_eligible, unbarred = (
        eligible[:k],
        eligible[k : 2 * k],
        eligible[2 * k :],
    )
    np.testing.assert_array_equal(redrawn_eligible, entered)
    barred = np.zeros(k, dtype=bool)
    for variable in variables:
        barred |= np.array(entries[variable]) > 0
    np.testing.assert_array_equal(entered, unbarred & ~barred)
    if (unbarred & barred).any():
        event("an entered award bars an otherwise eligible family")
    if (unbarred & ~barred).any():
        event("an entered zero leaves a family eligible")
