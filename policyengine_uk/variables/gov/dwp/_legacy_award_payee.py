"""Who is "on" a legacy income-related award."""

from policyengine_uk.model_api import *
from policyengine_uk.utils.benefit_unit import (
    CLAIMANT_OR_PARTNER_AWARDS,
    HALF_PENNY,
    REPORT_CLOSED,
)
from policyengine_uk.variables.gov.dwp.esa_income import (
    income_related_esa_award_on_reports,
)

# The award each formula gives on open person reports, for an award with
# closures of its own beyond the legacy closure (REPORT_CLOSED).
AWARD_ON_REPORTS = {"esa_income": income_related_esa_award_on_reports}


def is_payee_of_couple_award(person, period, reported, can_claim=None, couple=None):
    """Whether the claimant's or partner's family award is payable to this
    person. A person is on income-based JSA or income-related ESA on a day
    the allowance "is payable to him" (HB Regs 2006 reg 2(3) and (3A)); a
    person on Income Support is one "in receipt of" it (reg 2(1)). A couple's
    award is paid to the claimant, not the partner. The payee is the
    claimant or partner who reports the award, or the claimant where neither
    does (an award entered directly). Another member's report never moves
    the payee.

    can_claim, if given, limits the payee to the members of the couple who
    can be the claimant (for Pension Credit, those who have attained the
    qualifying age). Where neither can, both are considered, so a positive
    award entered for the couple is still paid to one of them.

    couple, if given (a person-level mask), replaces the claimant and
    partner (is_claimant_or_partner) where a rule reads another couple, such
    as the benefit cap's (benefit_cap_couple)."""
    claimant_or_partner = (
        person("is_claimant_or_partner", period) if couple is None else couple
    )
    if can_claim is not None:
        able = claimant_or_partner & can_claim
        claimant_or_partner = where(person.benunit.any(able), able, claimant_or_partner)
    reports = (person(reported, period) > 0) & claimant_or_partner
    head = claimant_or_partner & person("is_benunit_head", period)
    eldest = claimant_or_partner & (
        person.get_rank(
            person.benunit, -person("age", period), condition=claimant_or_partner
        )
        == 0
    )
    claimant = where(person.benunit.any(head), head, eldest)
    return where(person.benunit.any(reports), reports, claimant)


def own_report_is_paid(person, period, award, works, capital_limit):
    """Whether income-related ESA or income-based JSA (award: "esa_income" or
    "jsa_income") is paid on this person's own report, for a member who is
    neither the claimant nor the partner and so claims in their own right.

    Their claim is screened on them alone. They must not be engaged in
    remunerative work as its claimant (works), and the award on their report
    alone must be positive: the report exceeds the tariff income from the
    benefit unit's capital, within the capital limit (capital_limit). Their
    own capital is not observed, so the benefit unit's stands in for it.
    The benefit unit's screen (esa_income_eligible or jsa_income_eligible)
    cannot stand in for theirs, because when the claimant or partner reports
    an award it tests only them.

    Their own legacy benefits must remain open under the existing annual
    proxy (person_legacy_benefits_closed). A couple's closure does not end
    this separate claim. Income-related ESA also closes reports of its own
    (REPORT_CLOSED: its abolition, esa_income_report_closed). For it,
    own_report_is_paid compares the held award with the formula on open
    reports (AWARD_ON_REPORTS), both the benefit unit's award and the
    claimant's and partner's part of it (holds_formula_award). When both
    match, it applies the ESA report closure. When either differs, it
    applies only the person's legacy closure, and the benefit unit's held
    award decides payment. That award covers the whole unit, so an outside
    member with an open report stays paid while the unit's award stays
    positive, even if it leaves them nothing. The amounts can differ when a
    user enters esa_income, a reform replaces it, or
    disable_simulated_benefits holds both amounts in every year. The
    comparison can't separate two or more outside reporters in one benefit
    unit when the held total and the couple's part both equal the
    formula's: own_report_is_paid then applies each one's report
    closure. The benefit unit's award must also be in payment:
    positive, or nil while its work/capital screen fails and the award is not
    neutralised. A directly entered or reformed nil removes status while
    that screen passes; neutralising the award always removes it. These
    existing value-based override rules and shared-capital proxy are retained.
    """
    benunit = person.benunit
    own_award = (
        ~works
        & (benunit(f"{award}_assessable_capital", period) <= capital_limit)
        & (
            person(f"{award}_reported", period)
            > benunit(f"{award}_tariff_income", period)
        )
    )
    closed = person("person_legacy_benefits_closed", period)
    if award in AWARD_ON_REPORTS:
        units = person.simulation.populations["benunit"]
        report_closed = person(REPORT_CLOSED[award], period)
        as_formula = holds_formula_award(units, period, award)
        closed = where(units.project(as_formula), report_closed, closed)
    removed = person.simulation.tax_benefit_system.get_variable(award).is_neutralized
    paid = benunit(award, period) > 0
    screen_fails = ~benunit(f"{award}_eligible", period)
    return own_award & ~closed & (paid | (screen_fails & (not removed)))


def holds_formula_award(benunit, period, award):
    """Whether each benefit unit holds its formula's award (award:
    "esa_income"): both the stored award and the claimant's and partner's
    part of it (claimant_or_partner_esa_income) equal the formula in
    AWARD_ON_REPORTS on open person reports, compared to within half a
    penny at the precision the model stores each in.

    benunit is the simulation's benefit-unit population. Under
    disable_simulated_benefits the two held amounts differ from the
    formula's split even where the held total equals the formula's: with
    £5,200 held for the family and £5,000 for the claimant and partner, an
    outside adult holds £200, whatever the claimant's own open report gives.

    When the model calculates both, they always match. esa_income applies
    the formula to open reports, and claimant_or_partner_award applies the
    same formula to the claimant's and partner's open reports. It sets that
    part to zero only where the part, or the stored total that bounds it,
    falls within half a penny of zero, so the formula's part then falls
    within half a penny of zero too.
    """
    award_on_reports = AWARD_ON_REPORTS[award]
    person = benunit.members
    open_reported = person(f"{award}_reported", period) * ~person(
        REPORT_CLOSED[award], period
    )
    couple = person("is_claimant_or_partner", period)
    held = (
        (benunit(award, period), award_on_reports(benunit, period, open_reported)),
        (
            benunit(CLAIMANT_OR_PARTNER_AWARDS[award], period),
            award_on_reports(benunit, period, open_reported, couple),
        ),
    )
    return np.logical_and.reduce(
        [
            np.isclose(stored, formula.astype(stored.dtype), rtol=0, atol=HALF_PENNY)
            for stored, formula in held
        ]
    )
