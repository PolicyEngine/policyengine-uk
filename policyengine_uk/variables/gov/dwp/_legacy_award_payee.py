"""Who is "on" a legacy income-related award."""

from policyengine_uk.model_api import *


def is_payee_of_couple_award(person, period, reported):
    """Whether the claimant's or partner's family award is payable to this
    person. A person is on income-based JSA or income-related ESA on a day
    the allowance "is payable to him" (HB Regs 2006 reg 2(3) and (3A)); a
    person on Income Support is one "in receipt of" it (reg 2(1)). A couple's
    award is paid to the claimant, not the partner. The payee is the
    claimant or partner who reports the award, or the claimant where neither
    does (an award entered directly). Another member's report never moves
    the payee."""
    claimant_or_partner = person("is_claimant_or_partner", period)
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

    The benefit unit's award must also be in payment: positive, or nil only
    because the benefit unit's screen fails. When the award on this person's
    report alone is positive, that screen fails only when the claimant or
    partner reports an award and fails the work tests, which leaves this
    person's own claim standing. So a reform that neutralises the benefit
    removes the status, as does one that replaces the award with nil, or a
    nil award entered directly, while the screen passes.

    On the formula path another member's report or work never changes this.
    Their own tests read only their own work, their own report and the
    household's capital, and when the award on their report alone is
    positive, the benefit unit's award is positive exactly when its screen
    passes."""
    benunit = person.benunit
    own_award = (
        ~works
        & (benunit(f"{award}_assessable_capital", period) <= capital_limit)
        & (
            person(f"{award}_reported", period)
            > benunit(f"{award}_tariff_income", period)
        )
    )
    removed = person.simulation.tax_benefit_system.get_variable(award).is_neutralized
    paid = benunit(award, period) > 0
    screen_fails = ~benunit(f"{award}_eligible", period)
    return own_award & (paid | (screen_fails & (not removed)))
