"""Benefit-unit aggregation helpers for means tests."""


def add_for_claimant_and_partner(benunit, period, variables):
    """Sum variables over the benefit unit's claimant and partner.

    Means tests assess the income of the claimant and any partner, not of
    children, young persons or other members of the benefit unit (UC Regs
    2013 reg 22; HB Regs 2006 reg 25; IS Regs 1987 reg 23; TCA 2002 s.7;
    CTR (Prescribed Requirements) (England) Regs 2012 Sch 1 para 11).
    Person-level variables are summed over members flagged
    ``is_claimant_or_partner``; benefit-unit variables are added as they are.
    """
    person = benunit.members
    claimant_or_partner = person("is_claimant_or_partner", period)
    total = 0
    for name in variables:
        if person.entity.get_variable(name).entity.is_person:
            total = total + benunit.sum(person(name, period) * claimant_or_partner)
        else:
            total = total + benunit(name, period)
    return total
