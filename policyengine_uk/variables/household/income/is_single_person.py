from policyengine_uk.model_api import *


class is_single_person(Variable):
    value_type = bool
    entity = BenUnit
    label = "Single claimant"
    documentation = (
        "A claimant who has no partner and is not a lone parent, as defined "
        "for Housing Benefit and council tax reduction."
    )
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/2"

    def formula(benunit, period, parameters):
        return benunit("is_single", period) & ~benunit(
            "is_responsible_for_child_or_young_person_for_legacy_benefits", period
        )
