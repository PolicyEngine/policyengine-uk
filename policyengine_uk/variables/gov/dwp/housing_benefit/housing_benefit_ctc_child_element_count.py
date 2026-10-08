from policyengine_uk.model_api import *


class housing_benefit_ctc_child_element_count(Variable):
    value_type = int
    entity = BenUnit
    definition_period = YEAR
    label = "housing benefit ctc child element count"
    documentation = "Number of current family children whose individual elements were included in an actual CTC award, including a zero-payable award. Not inferred from benefit amounts; supply when known."
    reference = (
        "https://www.legislation.gov.uk/uksi/2017/376/made",
        "https://www.legislation.gov.uk/nisr/2017/79/made",
        "https://www.legislation.gov.uk/uksi/2024/611/regulation/6",
        "https://www.legislation.gov.uk/nisr/2024/119/regulation/5",
        "https://www.legislation.gov.uk/uksi/2026/316/regulation/2",
        "https://www.legislation.gov.uk/nisr/2026/68/regulation/2",
    )
