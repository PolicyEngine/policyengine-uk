from policyengine_uk.model_api import *


class is_responsible_for_child_or_young_person_for_legacy_benefits(Variable):
    value_type = bool
    entity = BenUnit
    label = "Responsible for a child or young person for legacy means-tested benefits"
    documentation = (
        "Whether the claimant or partner is responsible for a child or young "
        "person in the same household, using benefit-unit membership."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
    )

    def formula(benunit, period, parameters):
        return benunit.any(
            benunit.members("is_child_or_young_person_for_legacy_benefits", period)
        )
