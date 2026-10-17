"""Benefit-unit aggregation helpers for means tests."""

import numpy as np

# The tolerance for reading a stored award: values within half a penny of
# each other are the same, and an award within half a penny of zero is none.
HALF_PENNY = 0.005


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


def has_sixteen_year_old_dependant(benunit, period):
    """Whether a member aged 16 who is not the claimant or partner is present.

    Such a member is a dependant for part of the year under either scheme,
    whatever their education: Universal Credit makes them a qualifying young
    person up to the 1 September after their 16th birthday (UC Regs 2013
    reg. 5(1)(a)), and Housing Benefit takes the Child Benefit qualifying
    young person (HB Regs 2006 reg. 19(1)), which a school leaver remains
    until a terminal date or the end of an extension period (Child Benefit
    (General) Regulations 2006 regs. 5 and 7). Annual ages cannot place
    those dates, so the benefit cap rates, which turn on responsibility for a
    child or young person, count such a member for the year. The Housing
    Benefit cap exceptions read the model's Child Benefit qualifying young
    person instead, which leaves out a 16-year-old in neither non-advanced
    education nor approved training (#2287).
    """
    person = benunit.members
    age = person("age", period)
    return benunit.any(
        (age >= 16) & (age < 17) & ~person("is_claimant_or_partner", period)
    )


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
        stored_award, award_on_all_reports.astype(stored), rtol=0, atol=HALF_PENNY
    )
    as_reported_total = np.isclose(
        stored_award, reported_total.astype(stored), rtol=0, atol=HALF_PENNY
    )
    scoped = np.where(
        as_formula,
        award_on_members_reports,
        np.where(as_reported_total, members_reported, stored_award),
    )
    return np.where(stored_award > 0, scoped, 0)


def claimant_or_partner_award(benunit, period, award, reported, award_on_reports):
    """The claimant's and partner's part of a stored benefit-unit award.

    ``award`` names the stored award (esa_income or jsa_income), which covers
    every member of the benefit unit, and ``reported`` the person-level
    reported amount it is built from. ``award_on_reports(benunit, period,
    amount)`` is the award paid on a reported amount: the benefit's screen
    and tariff income (income_related_esa_award, income_related_jsa_award).

    This is award_of_members for the claimant and partner, so which awards
    the stored value holds is decided by its value, compared in the
    precision it is stored in, to within half a penny:

    - equal to the award on everyone's reports (its formula's result), the
      claimant's and partner's part is the award on their own reports;
    - otherwise, equal to the plain total of everyone's reports, the
      claimant's and partner's part is the plain total of their own reports;
    - anything else (an award entered directly, or a reform that replaces or
      scales it) is taken to be wholly the claimant's or partner's.

    An award within half a penny of zero is no award, whether stored or
    worked out here: a stored zero gives zero, and so does the float residual
    of about £0.000002 left by reports that exactly match the tariff income.

    The claimant_or_partner_* variables use this as their formula, and every
    reader of the claimant's or partner's award, the Income Support gate
    included, reads those variables. So an award set on them directly (as
    disable_simulated_benefits does for each year) is read the same way
    everywhere.
    """
    stored = benunit(award, period)
    scoped = award_of_members(
        benunit,
        period,
        award,
        reported,
        award_on_reports,
        benunit.members("is_claimant_or_partner", period),
    )
    return np.where((stored > HALF_PENNY) & (scoped > HALF_PENNY), scoped, 0)
