from policyengine_uk.model_api import *


class limited_capability_for_work_days(Variable):
    value_type = int
    entity = Person
    definition_period = YEAR
    label = "limited capability for work days"
    documentation = "Duration of the person's current legally linked ESA limited-capability-for-work period. Defaults to zero/false when the factual history is not supplied."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
    )
