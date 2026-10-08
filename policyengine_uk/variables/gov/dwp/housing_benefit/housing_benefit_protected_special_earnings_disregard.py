from policyengine_uk.model_api import *


class housing_benefit_protected_special_earnings_disregard(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "housing benefit protected special earnings disregard"
    documentation = "The person had a £20 HB earnings disregard within eight weeks before reaching Pension Credit qualifying age and continued employment after that award. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
