from policyengine_uk.model_api import *


class incapacity_for_work_gap_days(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "incapacity for work gap days"
    documentation = "Longest intervening break in the supplied linked incapacity periods. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
