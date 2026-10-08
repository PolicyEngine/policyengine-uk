from policyengine_uk.model_api import *


class esa_limited_capability_for_work_determined(Variable):
    value_type = bool
    entity = Person
    definition_period = YEAR
    label = "esa limited capability for work determined"
    documentation = "Secretary of State has determined that the person has, or is treated as having, limited capability for work for ESA. This is not the separate Universal Credit status."
    reference = (
        "https://www.legislation.gov.uk/uksi/2002/1792/schedule/VI",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/4",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
    )
