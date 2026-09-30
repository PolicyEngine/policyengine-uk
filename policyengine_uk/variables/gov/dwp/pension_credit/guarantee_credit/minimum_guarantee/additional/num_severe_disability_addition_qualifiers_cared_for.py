from policyengine_uk.model_api import *


class num_severe_disability_addition_qualifiers_cared_for(Variable):
    value_type = int
    entity = BenUnit
    label = (
        "Qualifying claimants or partners with a carer benefit paid for caring for them"
    )
    documentation = (
        "How many of the claimant and partner who receive a qualifying "
        "disability benefit have someone entitled to and in receipt of "
        "Carer's Allowance or Carer Support Payment in respect of caring for "
        "them. The data do not say whom a carer cares for. A carer benefit "
        "needs the person cared for to receive a qualifying disability "
        "benefit, and each award is for one person (SSCBA 1992 s.70(7)), so "
        "each carer is attributed as follows. A claimant or partner cares for "
        "their partner if the partner qualifies; any other member of a benefit "
        "unit cares for a qualifying claimant or partner of that unit if there "
        "is one. No one is their own carer. The household's other carers are "
        "allocated to qualifying claimants or partners not yet cared for in "
        "the other benefit units, one each, taking the units in descending "
        "order of their eldest member's age. Carers outside the household, and "
        "Universal Credit awards that include the carer element, are not "
        "counted. Reading Universal Credit here would be circular, because the "
        "Universal Credit non-dependant deduction exemption reads Pension "
        "Credit; a Universal Credit carer in the household already stops the "
        "addition through the residence condition unless their presence is "
        "ignored. Receipt is receives_carer_benefit, so it inherits "
        "carers_allowance, which does not apply the overlapping-benefit rule "
        "that stops Carer's Allowance being paid alongside a higher State "
        "Pension."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
        "https://www.legislation.gov.uk/ukpga/1992/4/section/70",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        qualifies = claimant_or_partner & person(
            "receives_severe_disability_addition_qualifying_benefit", period
        )
        carer = person("receives_carer_benefit", period)
        qualifying = benunit.sum(qualifies)
        # Carers within their own unit: there is a qualifying claimant or
        # partner in the carer's unit other than the carer.
        qualifiers_in_own_unit = benunit.project(qualifying) - qualifies
        cares_within_unit = carer & (qualifiers_in_own_unit > 0)
        cared_for_within = min_(qualifying, benunit.sum(cares_within_unit))
        not_yet_cared_for = qualifying - cared_for_within
        # Every other carer benefit is for someone in another unit.
        cares_outside_unit = carer & ~cares_within_unit
        outside_here = benunit.sum(cares_outside_unit)
        outside_in_household = benunit.max(person.household.sum(cares_outside_unit))
        # Order the household's units by their eldest member (ties by position)
        # and give each unit, in turn, carers from the other units.
        age = person("age", period)
        representative = person.get_rank(person.benunit, -age) == 0
        order = person.get_rank(person.household, -age, condition=representative)
        unit_order = benunit.max(where(representative, order, -1))
        allocated_in_household = np.zeros_like(outside_here)
        cared_for_from_other_units = np.zeros_like(outside_here)
        for rank in range(int(np.max(unit_order, initial=-1)) + 1):
            available = max_(
                0,
                min_(
                    outside_in_household - outside_here,
                    outside_in_household - allocated_in_household,
                ),
            )
            allocated = where(unit_order == rank, min_(not_yet_cared_for, available), 0)
            cared_for_from_other_units = cared_for_from_other_units + allocated
            allocated_by_representative = where(
                representative, benunit.project(allocated), 0
            )
            allocated_in_household = allocated_in_household + benunit.max(
                person.household.sum(allocated_by_representative)
            )
        return cared_for_within + cared_for_from_other_units
