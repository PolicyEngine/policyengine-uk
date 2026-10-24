"""Benefit-unit aggregation helpers for means tests."""

import numpy as np

# The tolerance for reading a stored award: values within half a penny of
# each other are the same, and an award within half a penny of zero is none.
HALF_PENNY = 0.005

# For each award award_of_members reads, the person-level variable saying the
# award on a member's report has ended. Its formula leaves those reports out:
# income-related ESA also ends for the claimant and partner of a family that
# claims Universal Credit (esa_income_report_closed).
REPORT_CLOSED = {
    "esa_income": "esa_income_report_closed",
    "jsa_income": "person_legacy_benefits_closed",
}


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
    person, which counts a 16-year-old for the year too, whatever their
    education (Child Benefit (General) Regulations 2006 reg. 4).
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
    when it holds the plain total of the reports (as the
    disable_simulated_benefits reform sets it in the dataset year), this is
    the plain total of their reports; when it holds anything else (an award
    entered directly, or a reform that replaces it), that value is taken to
    be theirs. Values are compared to within half a penny after rounding to
    the precision ``award`` is stored in. A stored zero is zero.

    In a later year the reform's held award is neither, so this takes all of
    it, another member's award included, to be the members'. So readers of
    the claimant's and partner's award read the claimant_or_partner_*
    variables, which the reform sets: the means tests, the passports and the
    Income Support gate directly, and the benefit cap through
    award_of_couple.
    """
    person = benunit.members
    stored_award = benunit(award, period)
    reported = person(report, period)
    reported_total = benunit.sum(reported)
    members_reported = benunit.sum(reported * members)
    # Formula awards omit reports whose own award has closed. Keep the raw
    # totals above for disable_simulated_benefits and direct-value provenance.
    open_reported = reported * ~person(REPORT_CLOSED[award], period)
    award_on_all_reports = award_on_reports(benunit, period, benunit.sum(open_reported))
    award_on_members_reports = award_on_reports(
        benunit, period, benunit.sum(open_reported * members)
    )
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
    reader of the claimant's or partner's award reads those variables: the
    means tests, the passports and the Income Support gate directly, and the
    benefit cap through award_of_couple. So an award set on them directly (as
    disable_simulated_benefits does for each year) is read the same way
    everywhere. The one exception is a Universal Credit couple that is not
    the claimant and partner (award_of_couple).
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


# The variable holding the claimant's and partner's part of each benefit-unit
# award; claimant_or_partner_award is its formula.
CLAIMANT_OR_PARTNER_AWARDS = {
    "esa_income": "claimant_or_partner_esa_income",
    "jsa_income": "claimant_or_partner_jsa_income",
}


def award_of_couple(benunit, period, award, reported, award_on_reports, couple):
    """The part of the benefit-unit award ``award`` that ``couple`` claim.

    ``award`` is esa_income or jsa_income, and ``couple`` a person-level
    boolean array: the single person or couple a rule reads (the benefit
    cap's couple, for example). Where ``couple`` is the claimant and partner
    (is_claimant_or_partner) for every member of the benefit unit, this is
    their award, the claimant_or_partner_* variable for ``award``, so a value
    set on it (as disable_simulated_benefits does for each year) or entered
    directly is read here as everywhere else. In formula mode that equals
    award_of_members for ``couple``, except that an award within half a
    penny of zero is no award. Otherwise it is award_of_members for
    ``couple``, read from the stored award by value. That is a Universal
    Credit couple that is not the claimant and partner, which takes an
    entered is_uc_claimant or is_uc_assessed_claimant, or more than two
    members entered as claimant or partner; under disable_simulated_benefits
    it still takes another member's held award to be the couple's after the
    dataset year.
    """
    person = benunit.members
    same_couple = ~benunit.any(couple != person("is_claimant_or_partner", period))
    claimant_or_partner = benunit(CLAIMANT_OR_PARTNER_AWARDS[award], period)
    if np.all(same_couple):
        return claimant_or_partner
    return np.where(
        same_couple,
        claimant_or_partner,
        award_of_members(benunit, period, award, reported, award_on_reports, couple),
    )
