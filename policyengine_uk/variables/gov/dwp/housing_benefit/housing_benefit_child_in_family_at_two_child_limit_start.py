from policyengine_uk.model_api import *


class housing_benefit_child_in_family_at_two_child_limit_start(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit child in family at two child limit start"
    documentation = "This current family child was an individual for whom the claimant was responsible immediately before the jurisdiction's 2017 child-limit cutoff. Not inferred from benefit amounts; supply when known."
    reference = (
        "https://www.legislation.gov.uk/uksi/2017/376/made",
        "https://www.legislation.gov.uk/nisr/2017/79/made",
        "https://www.legislation.gov.uk/uksi/2024/611/regulation/6",
        "https://www.legislation.gov.uk/nisr/2024/119/regulation/5",
        "https://www.legislation.gov.uk/uksi/2026/316/regulation/2",
        "https://www.legislation.gov.uk/nisr/2026/68/regulation/2",
    )
