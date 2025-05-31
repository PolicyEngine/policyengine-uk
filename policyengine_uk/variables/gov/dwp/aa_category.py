from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_or_higher import (
    LowerOrHigher,
)


class aa_category(Variable):
    label = "Attendance Allowance category"
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerOrHigher
    default_value = LowerOrHigher.NONE

    def formula(person, period, parameters):
        aa = parameters(period).baseline.gov.dwp.attendance_allowance
        SAFETY_MARGIN = 0.1  # Survey reported values could be slightly below eligible values when they should be above due to data manipulation
        reported_weekly_aa = (
            person("attendance_allowance_reported", period) / WEEKS_IN_YEAR
        )
        return select(
            [
                reported_weekly_aa >= aa.higher * (1 - SAFETY_MARGIN),
                reported_weekly_aa >= aa.lower * (1 - SAFETY_MARGIN),
            ],
            [LowerOrHigher.HIGHER, LowerOrHigher.LOWER],
            default=LowerOrHigher.NONE,
        )
