from policyengine_uk.model_api import *


class lha_renter_has_non_dependant(Variable):
    value_type = bool
    entity = BenUnit
    label = "LHA renter has a non-dependant (household composition proxy)"
    documentation = (
        "A conservative proxy: a claimant or partner of another benefit unit "
        "in the household, or someone in this benefit unit who is neither a "
        "claimant/partner nor a UC child or qualifying young person. The model "
        "does not identify the statutory exclusions for joint renters, "
        "commercial lodgers, landlords or foster children here. Rent liability "
        "alone does not exclude another benefit unit's claimant."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/9",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        # A child or young person under either scheme (UC reg 5; HB reg 19)
        # is a dependant, not a non-dependant.
        age = person("age", period)
        child_or_qyp = (
            person("is_child_or_qualifying_young_person_for_universal_credit", period)
            | person("is_child_or_young_person_for_legacy_benefits", period)
            | ((age >= 16) & (age < 17))
        )
        within_benefit_unit = benunit.any(~claimant_or_partner & ~child_or_qyp)
        other_benefit_unit_claimants = benunit.max(
            person.household.sum(claimant_or_partner)
        ) - benunit.sum(claimant_or_partner)
        return within_benefit_unit | (other_benefit_unit_claimants > 0)
