from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_or_higher import (
    LowerOrHigher,
)


class dla_m_category(Variable):
    label = "DLA (mobility) category"
    documentation = "If you receive the mobility component of Disability Living Allowance, you will be in one of the following categories: Lower, Higher. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerOrHigher
    default_value = LowerOrHigher.NONE

    def formula(person, period, parameters):
        dla_m = parameters(period).baseline.gov.dwp.dla.mobility
        SAFETY_MARGIN = 0.1  # Survey reported values could be slightly below eligible values when they should be above due to data manipulation
        reported_weekly_dla_m = (
            person("dla_m_reported", period) / WEEKS_IN_YEAR
        )
        return select(
            [
                reported_weekly_dla_m >= dla_m.higher * (1 - SAFETY_MARGIN),
                reported_weekly_dla_m >= dla_m.lower * (1 - SAFETY_MARGIN),
                True,
            ],
            [
                LowerOrHigher.HIGHER,
                LowerOrHigher.LOWER,
                LowerOrHigher.NONE,
            ],
        )
