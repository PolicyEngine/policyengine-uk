from policyengine_uk.model_api import *


class is_housing_benefit_young_individual(Variable):
    value_type = bool
    entity = BenUnit
    label = "Young individual (Housing Benefit)"
    documentation = (
        "A single claimant (no partner and not a lone parent) under the "
        "shared accommodation age threshold, other than one who requires "
        "overnight care (see meets_lha_overnight_care_condition) or is a "
        "qualifying parent or carer (see "
        "is_housing_benefit_qualifying_parent_or_carer). The exceptions for "
        "a housing association landlord, care leavers, former hostel "
        "residents, offenders under multi-agency management, and victims of "
        "domestic violence and of modern slavery are not identified."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/2"

    def formula(benunit, period, parameters):
        threshold = parameters(period).gov.dwp.LHA.shared_accommodation_age_threshold
        person = benunit.members
        # HB Regs 2006 reg 2(1), "young individual": not a claimant who is a
        # person who requires overnight care or a qualifying parent or carer.
        requires_overnight_care = benunit.any(
            person("is_claimant_or_partner", period)
            & person("meets_lha_overnight_care_condition", period)
        )
        return (
            benunit("is_single_person", period)
            & (benunit("eldest_claimant_or_partner_age", period) < threshold)
            & ~requires_overnight_care
            & ~benunit("is_housing_benefit_qualifying_parent_or_carer", period)
        )
