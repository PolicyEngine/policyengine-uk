"""Who is "on" a legacy income-related award."""

from policyengine_uk.model_api import *


def is_payee_of_couple_award(person, period, reported, can_claim=None):
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
    award entered for the couple is still paid to one of them."""
    claimant_or_partner = person("is_claimant_or_partner", period)
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


def own_report_is_paid(person, period, award):
    """Whether income-related ESA or income-based JSA (award: "esa_income" or
    "jsa_income") is paid on this person's own report, for a member who is
    neither the claimant nor the partner and so claims in their own right.
    It is paid when the award on their report alone is positive: the report
    exceeds the tariff income from the benefit unit's capital, within the
    capital limit, as income_related_esa_award and income_related_jsa_award
    screen it. Their own capital is not observed, so the benefit unit's
    stands in for it. The benefit unit's award must also be positive, so a
    reform that removes or zeroes the benefit removes the status too.

    Another member's report never changes this: once this person reports,
    the capital test reads the household's capital whoever else reports, and
    the award on their report alone does not depend on other reports. On the
    formula path a positive award on their report implies a positive benefit
    unit award, since adding reports never lowers it."""
    benunit = person.benunit
    return (
        benunit(f"{award}_eligible", period)
        & (
            person(f"{award}_reported", period)
            > benunit(f"{award}_tariff_income", period)
        )
        & (benunit(award, period) > 0)
    )
