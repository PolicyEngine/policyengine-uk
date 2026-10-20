from policyengine_uk.model_api import *


class uc_unable_to_provide_childcare(Variable):
    value_type = bool
    entity = Person
    label = "Unable to provide childcare for the Universal Credit work condition"
    documentation = (
        "Regulation 32(1)(b): the other member of a couple who is not in paid "
        "work still lets the claimant meet the work condition if they are "
        "unable to provide childcare because they (i) have limited capability "
        "for work, (ii) have regular and substantial caring responsibilities "
        "for a severely disabled person, or (iii) are temporarily absent from "
        "the claimant's household. Each limb is an approximation. Limb (i) "
        "reads uc_limited_capability_for_work, which is limited capability "
        "for work and work-related activity (uc_limited_capability_for_WRA) "
        "or else is_disabled_for_benefits (disability benefit receipt in "
        "survey data), not an observed work capability assessment. An ESA "
        "award without the support component removes limited capability for "
        "work-related activity but not for work, so it still meets limb (i). "
        "Limb (ii), defined in regulation 30, reads "
        "is_carer_for_benefits: receipt of Carer's Allowance or Carer Support "
        "Payment, or at least the Carer's Allowance qualifying hours of care "
        "a week. Its hours branch does not check that the person cared for "
        "is severely disabled (a Carer's Allowance condition, SSCBA 1992 "
        "s. 70(1)-(2), that regulation 30(1)(a) imports) or exclude a carer "
        "paid for the caring (regulation 30(3)). Limb (iii) is the input "
        "uc_is_temporarily_absent_from_claimant_household."
    )
    definition_period = YEAR
    reference = [
        dict(
            title="Universal Credit Regulations 2013 reg. 32(1)(b)",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/32",
        ),
        dict(
            title="Universal Credit Regulations 2013 reg. 30",
            href="https://www.legislation.gov.uk/uksi/2013/376/regulation/30",
        ),
        dict(
            title="Social Security Contributions and Benefits Act 1992 s. 70",
            href="https://www.legislation.gov.uk/ukpga/1992/4/section/70",
        ),
        dict(
            title="Advice for Decision Making ch. F7, para. F7013",
            href="https://assets.publishing.service.gov.uk/media/696a076c7b7f37aa8e4022d9/adm-ch-f7.pdf",
        ),
    ]

    def formula(person, period, parameters):
        return (
            person("uc_limited_capability_for_work", period)
            | person("is_carer_for_benefits", period)
            | person("uc_is_temporarily_absent_from_claimant_household", period)
        )
