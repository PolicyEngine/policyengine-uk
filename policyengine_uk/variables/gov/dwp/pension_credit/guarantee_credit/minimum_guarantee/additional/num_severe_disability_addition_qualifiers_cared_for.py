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
        "them. The data do not say whom a carer cares for, so: a claimant's or "
        "partner's own carer benefit is for their partner if the partner "
        "qualifies, and otherwise for someone else (no one is their own "
        "carer, and a carer benefit needs the person cared for to receive a "
        "qualifying disability benefit); a carer benefit received by anyone "
        "else in the household is for a qualifying claimant or partner, each "
        "for a different one. Carers outside the household, and Universal "
        "Credit awards that include the carer element, are not counted. "
        "Reading Universal Credit here would be circular, because the "
        "Universal Credit non-dependant deduction exemption reads Pension "
        "Credit; a Universal Credit carer in the household already stops the "
        "addition through the residence condition unless their presence is "
        "ignored."
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
        partner_qualifies = claimant_or_partner & (
            benunit.project(qualifying) - qualifies > 0
        )
        partner_carers = benunit.sum(claimant_or_partner & carer & partner_qualifies)
        household_carers = benunit.max(person.household.sum(carer))
        other_carers = household_carers - benunit.sum(claimant_or_partner & carer)
        return min_(qualifying, partner_carers + other_carers)
