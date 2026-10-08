from policyengine_uk.model_api import *


class meets_severe_disability_addition_residence_condition(Variable):
    value_type = bool
    entity = BenUnit
    label = "Meets the Pension Credit severe disability addition residence condition"
    documentation = (
        "No person aged 18 or over, other than one whose presence is ignored, "
        "normally resides with the claimant (and partner). Everyone else in the "
        "household counts, including a member of the benefit unit who is "
        "neither the claimant, the partner nor a qualifying young person. "
        "The pension-age Housing Benefit severe disability premium applies a "
        "similar test to non-dependants (HB(SPC) Regs 2006 Sch 3 para "
        "6(2)(a)(ii), (b)(iii) and (6)), which also counts a young person of "
        "another family."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/I/paragraph/2",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3/paragraph/6",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        counted = person("is_counted_resident_for_severe_disability_addition", period)
        claimant_or_partner = person("is_claimant_or_partner", period)
        counted_in_household = benunit.max(person.household.sum(counted))
        counted_claimants_or_partners = benunit.sum(counted & claimant_or_partner)
        return counted_in_household == counted_claimants_or_partners
