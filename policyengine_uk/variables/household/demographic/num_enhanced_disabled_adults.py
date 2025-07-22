from policyengine_uk.model_api import *


class num_enhanced_disabled_adults(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of enhanced disabled adults"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        adult = benunit.members("is_adult", period)
        enhanced_disabled = benunit.members(
            "is_enhanced_disabled_for_benefits", period
        )
        return benunit.sum(adult & enhanced_disabled)
