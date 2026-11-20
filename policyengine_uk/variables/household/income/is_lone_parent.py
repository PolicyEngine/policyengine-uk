from policyengine_uk.model_api import *


class is_lone_parent(Variable):
    value_type = bool
    entity = BenUnit
    label = "Lone parent"
    documentation = (
        "A claimant with no partner who is responsible for a child or young "
        "person in the same household, as defined for Income Support, "
        "Housing Benefit and council tax reduction."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2012/2885/regulation/2",
    )

    def formula(benunit, period, parameters):
        return benunit("is_single", period) & benunit(
            "is_responsible_for_child_or_young_person_for_legacy_benefits", period
        )
