"""Benefit-unit aggregation helpers for means tests."""

import numpy as np


def add_for_members(benunit, period, variables, members):
    """Sum variables over the benefit-unit members a means test counts.

    ``members`` is a person-level boolean array. Person-level variables are
    summed over those members only; benefit-unit variables are added as they
    are. Means tests pass the claimant and partner plus the programme's own
    children or young persons, so a member who is none of these (for example
    an 18-year-old who is neither a partner nor a qualifying young person)
    does not count. A benefit-unit variable must therefore already cover only
    those members: pass claimant_or_partner_esa_income and
    claimant_or_partner_jsa_income, not esa_income and jsa_income, which also
    hold awards that other members claim in their own right.
    """
    person = benunit.members
    total = 0
    for name in variables:
        if person.entity.get_variable(name).entity.is_person:
            total = total + benunit.sum(person(name, period) * members)
        else:
            total = total + benunit(name, period)
    return total


def claimant_or_partner_award(benunit, period, award, reported, award_on_reports):
    """The claimant's and partner's part of a stored benefit-unit award.

    ``award`` names the stored award (esa_income or jsa_income), which covers
    every member of the benefit unit, and ``reported`` the person-level
    reported amount it is built from. ``award_on_reports(benunit, period,
    amount)`` is the award paid on a reported amount: the benefit's screen
    and tariff income (income_related_esa_award, income_related_jsa_award).

    Which awards the stored value holds is decided by its value, compared in
    the precision it is stored in, to within half a penny:

    - equal to the award on everyone's reports (its formula's result), the
      claimant's and partner's part is the award on their own reports;
    - otherwise, equal to the plain total of everyone's reports, the
      claimant's and partner's part is the plain total of their own reports;
    - anything else (an award entered directly, or a reform that replaces or
      scales it) is taken to be wholly the claimant's or partner's.

    A stored award of zero or less gives zero. The claimant_or_partner_*
    variables use this as their formula, and every reader of the claimant's
    or partner's award, the Income Support gate included, reads those
    variables. So an award set on them directly (as disable_simulated_benefits
    does for each year) is read the same way everywhere.
    """
    person = benunit.members
    stored = benunit(award, period)
    amounts = person(reported, period)
    reported_total = benunit.sum(amounts)
    claimant_or_partner_reported = benunit.sum(
        amounts * person("is_claimant_or_partner", period)
    )
    # Compare in the stored precision (float32): the formula's own award must
    # match the award recomputed here in float64.
    precision = stored.dtype
    as_formula = np.isclose(
        stored,
        award_on_reports(benunit, period, reported_total).astype(precision),
        rtol=0,
        atol=0.005,
    )
    as_reported_total = np.isclose(
        stored, reported_total.astype(precision), rtol=0, atol=0.005
    )
    scoped = np.where(
        as_formula,
        award_on_reports(benunit, period, claimant_or_partner_reported),
        np.where(as_reported_total, claimant_or_partner_reported, stored),
    )
    return np.where(stored > 0, scoped, 0)
