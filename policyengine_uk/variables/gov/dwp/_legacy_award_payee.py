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
