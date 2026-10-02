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
        "the claimant's household. Limb (i) uses the model's limited "
        "capability proxy, uc_limited_capability_for_WRA (it defaults to "
        "is_disabled_for_benefits); limited capability for work and "
        "work-related activity includes limited capability for work. Limb "
        "(ii) uses is_carer_for_benefits, the regulation 30 test. Limb (iii) "
        "is the input uc_is_temporarily_absent_from_claimant_household."
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
            title="Advice for Decision Making ch. F7, para. F7013",
            href="https://assets.publishing.service.gov.uk/media/696a076c7b7f37aa8e4022d9/adm-ch-f7.pdf",
        ),
    ]

    def formula(person, period, parameters):
        return (
            person("uc_limited_capability_for_WRA", period)
            | person("is_carer_for_benefits", period)
            | person("uc_is_temporarily_absent_from_claimant_household", period)
        )
