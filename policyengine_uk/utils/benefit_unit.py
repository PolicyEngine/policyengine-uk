"""Benefit-unit aggregation helpers for means tests."""


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
