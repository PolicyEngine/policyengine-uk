from policyengine_uk.model_api import *


class incapacity_for_work_days(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "incapacity for work days"
    documentation = "Duration of the person's current legally linked incapacity-for-work period, with only breaks permitted by the relevant rule included. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
