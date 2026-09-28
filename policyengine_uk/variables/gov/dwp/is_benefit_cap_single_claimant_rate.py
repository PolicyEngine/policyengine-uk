from policyengine_uk.model_api import *


class is_benefit_cap_single_claimant_rate(Variable):
    value_type = bool
    entity = BenUnit
    label = "Benefit cap single claimant rate applies"
    documentation = (
        "Whether the claimant has no partner and is not responsible for a "
        "child or qualifying young person for Universal Credit. The model "
        "uses one benefit cap for Universal Credit and Housing Benefit. "
        "Housing Benefit instead uses the Child Benefit young-person "
        "definition. Couple status is a proxy for joint-claim status and "
        "does not capture Universal Credit couples who may claim as singles."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/80A",
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/75CA",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/2",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
    )

    def formula(benunit, period, parameters):
        return ~benunit("is_couple", period) & ~benunit(
            "is_responsible_for_child_or_qualifying_young_person_for_universal_credit",
            period,
        )
