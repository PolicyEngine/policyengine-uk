from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_middle_or_higher import (
    LowerMiddleOrHigher,
)


class dla_sc_category(Variable):
    label = "DLA (Self-care) category"
    documentation = "If you receive the self-care component of Disability Living Allowance, you will be in one of the following categories: Lower, Middle, Higher. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerMiddleOrHigher
    default_value = LowerMiddleOrHigher.NONE

    def formula(person, period, parameters):
        dla_sc = parameters(period).baseline.gov.dwp.dla.self_care
        SAFETY_MARGIN = 0.1  # Survey reported values could be slightly below eligible values when they should be above due to data manipulation
        reported_weekly_dla_sc = (
            person("dla_sc_reported", period) / WEEKS_IN_YEAR
        )
        return select(
            [
                reported_weekly_dla_sc >= dla_sc.higher * (1 - SAFETY_MARGIN),
                reported_weekly_dla_sc >= dla_sc.middle * (1 - SAFETY_MARGIN),
                reported_weekly_dla_sc >= dla_sc.lower * (1 - SAFETY_MARGIN),
                True,
            ],
            [
                LowerMiddleOrHigher.HIGHER,
                LowerMiddleOrHigher.MIDDLE,
                LowerMiddleOrHigher.LOWER,
                LowerMiddleOrHigher.NONE,
            ],
        )
