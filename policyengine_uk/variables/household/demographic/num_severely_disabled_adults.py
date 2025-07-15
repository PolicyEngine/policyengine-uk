from policyengine_uk.model_api import *


class num_severely_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of severely disabled adults"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        severely_disabled = benunit.members(
            "is_severely_disabled_for_benefits", period
        )
        return benunit.sum(adult & severely_disabled)
