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
        "them. The data do not say whom a carer cares for, and a carer benefit "
        "needs the person cared for to receive a qualifying disability "
        "benefit, so each carer is attributed as follows. A claimant or partner "
        "cares for their partner if the partner qualifies; any other member of "
        "a benefit unit cares for a qualifying claimant or partner of that "
        "unit if there is one. No one is their own carer. Every other carer "
        "benefit in the household is treated as paid for a qualifying claimant "
        "or partner of each other benefit unit there, each carer for a "
        "different one. Carers outside the household, and Universal Credit "
        "awards that include the carer element, are not counted. Reading "
        "Universal Credit here would be circular, because the Universal "
        "Credit non-dependant deduction exemption reads Pension Credit; a "
        "Universal Credit carer in the household already stops the addition "
        "through the residence condition unless their presence is ignored."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/regulation/6",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/6",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        qualifies = claimant_or_partner & person(
            "receives_severe_disability_addition_qualifying_benefit", period
        )
        carer = person("receives_carer_benefit", period)
        qualifying = benunit.sum(qualifies)
        # Qualifying claimants or partners in the carer's own unit, other than
        # the carer.
        qualifiers_in_own_unit = benunit.project(qualifying) - qualifies
        cares_within_unit = carer & (qualifiers_in_own_unit > 0)
        cares_outside_unit = carer & ~cares_within_unit
        within_unit = benunit.sum(cares_within_unit)
        from_other_units = benunit.max(
            person.household.sum(cares_outside_unit)
        ) - benunit.sum(cares_outside_unit)
        return min_(qualifying, within_unit + from_other_units)
