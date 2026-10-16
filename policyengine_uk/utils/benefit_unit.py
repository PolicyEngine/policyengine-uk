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


def award_of_members(benunit, period, award, report, award_on_reports, members):
    """The part of the benefit-unit award ``award`` that ``members`` claim.

    ``report`` is the person-level report behind the award and
    ``award_on_reports(benunit, period, reported)`` the award the formula of
    ``award`` gives on a reported amount. Which awards ``award`` holds is
    decided by value: when it holds the award its formula gives on all
    reported awards, this is the same award on the reports of ``members``;
    when it holds the plain total of the reports (the
    disable_simulated_benefits reform), this is the plain total of their
    reports; when it holds anything else (an award entered directly, or a
    reform that replaces it), that value is taken to be theirs. Values are
    compared to within half a penny after rounding to the precision
    ``award`` is stored in. A stored zero is zero.
    """
    person = benunit.members
    stored_award = benunit(award, period)
    reported = person(report, period)
    reported_total = benunit.sum(reported)
    members_reported = benunit.sum(reported * members)
    award_on_all_reports = award_on_reports(benunit, period, reported_total)
    award_on_members_reports = award_on_reports(benunit, period, members_reported)
    # Compare in the precision the award is stored in (float32), so the
    # formula's own award always matches the award recomputed here.
    stored = stored_award.dtype
    as_formula = np.isclose(
        stored_award, award_on_all_reports.astype(stored), rtol=0, atol=0.005
    )
    as_reported_total = np.isclose(
        stored_award, reported_total.astype(stored), rtol=0, atol=0.005
    )
    scoped = np.where(
        as_formula,
        award_on_members_reports,
        np.where(as_reported_total, members_reported, stored_award),
    )
    return np.where(stored_award > 0, scoped, 0)
