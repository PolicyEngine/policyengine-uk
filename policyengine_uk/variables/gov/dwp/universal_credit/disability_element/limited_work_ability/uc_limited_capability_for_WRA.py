from policyengine_uk.model_api import *


class uc_limited_capability_for_WRA(Variable):
    value_type = bool
    entity = Person
    label = "Assessed to have limited capability for work-related activity"
    documentation = "Whether this person has been assessed by the DWP as having limited capability for work or work-related activity"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("is_disabled_for_benefits", period)
