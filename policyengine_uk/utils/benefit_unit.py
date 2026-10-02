"""Benefit-unit aggregation helpers for means tests."""


def add_for_members(benunit, period, variables, members):
    """Sum variables over the benefit-unit members a means test counts.

    ``members`` is a person-level boolean array. Person-level variables are
    summed over those members only; benefit-unit variables are added as they
    are. Means tests pass the claimant and partner plus the programme's own
    children or young persons, so a member who is none of these (for example
    an 18-year-old who is neither a partner nor a qualifying young person)
    does not count.
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
    those dates, so the family rules that turn on responsibility for a child
    or young person count such a member for the year.
    """
    person = benunit.members
    age = person("age", period)
    return benunit.any(
        (age >= 16) & (age < 17) & ~person("is_claimant_or_partner", period)
    )
