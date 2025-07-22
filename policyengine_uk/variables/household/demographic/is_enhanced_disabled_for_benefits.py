from policyengine_uk.model_api import *


class is_enhanced_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Whether meets the middle disability benefit entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        dla_requirement = (
            parameters(period).gov.dwp.dla.self_care.higher * WEEKS_IN_YEAR
        )
        return person("dla_sc", period) >= dla_requirement
