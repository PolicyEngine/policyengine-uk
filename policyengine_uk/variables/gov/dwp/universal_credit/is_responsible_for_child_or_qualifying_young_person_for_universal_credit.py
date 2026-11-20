from policyengine_uk.model_api import *


class is_responsible_for_child_or_qualifying_young_person_for_universal_credit(
    Variable
):
    value_type = bool
    entity = BenUnit
    label = "Responsible for a child or qualifying young person for Universal Credit"
    documentation = (
        "Whether the claimant (or either joint claimant) is responsible for "
        "at least one child (under 16) or qualifying young person, using "
        "benefit-unit membership for 'normally lives with'."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/ukpga/2012/5/section/40",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/4",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/5",
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        return benunit.any(
            person("is_child_or_qualifying_young_person_for_universal_credit", period)
            & ~person("is_uc_claimant", period)
        )
