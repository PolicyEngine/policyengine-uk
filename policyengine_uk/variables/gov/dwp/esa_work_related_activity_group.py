from policyengine_uk.model_api import *


class esa_work_related_activity_group(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "esa work related activity group"
    documentation = "The Secretary of State has determined that this person belongs to the ESA work-related activity group. Not inferred from benefit amounts; supply when known."
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/1A",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/21",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4",
    )
