from policyengine_uk.model_api import *


class is_severely_disabled_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Has a severe disability"
    documentation = (
        "Whether this person is severely disabled for benefits purposes"
    )
    definition_period = YEAR
    reference = "Child Tax Credit Regulations 2002 s. 8"

    def formula(person, period, parameters):
        benefit = parameters(period).gov.dwp
        THRESHOLD_SAFETY_GAP = 10 * WEEKS_IN_YEAR
        paragraph_3 = (
            person("dla_sc", period)
            >= benefit.dla.self_care.higher * WEEKS_IN_YEAR
            - THRESHOLD_SAFETY_GAP
        )
        paragraph_4 = (
            person("pip_dl", period)
            >= benefit.pip.daily_living.enhanced * WEEKS_IN_YEAR
            - THRESHOLD_SAFETY_GAP
        )
        paragraph_5 = person("afcs", period) > 0
        return sum([paragraph_3, paragraph_4, paragraph_5]) > 0
