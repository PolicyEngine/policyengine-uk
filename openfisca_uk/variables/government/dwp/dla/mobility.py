from openfisca_uk.model_api import *
from openfisca_uk.variables.misc.categories.lower_or_higher import (
    LowerOrHigher,
)


class DLA_M_reported(Variable):
    value_type = float
    entity = Person
    label = "DLA (mobility) (reported)"
    definition_period = YEAR
    unit = "currency-GBP"


class dla_m_category(Variable):
    label = "DLA (mobility) category"
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerOrHigher
    default_value = LowerOrHigher.NONE

    def formula(person, period, parameters):
        dla_m = parameters(period).dwp.dla.mobility
        SAFETY_MARGIN = 0.1  # Survey reported values could be slightly below eligible values when they should be above due to data manipulation
        reported_weekly_dla_m = (
            person("DLA_M_reported", period) / WEEKS_IN_YEAR
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


class dla_m(Variable):
    label = "DLA (mobility)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(person, period, parameters):
        dla_m = parameters(period).dwp.dla.mobility
        category = person("dla_m_category", period)
        return (
            select(
                [
                    category == LowerOrHigher.HIGHER,
                    category == LowerOrHigher.LOWER,
                    category == LowerOrHigher.NONE,
                ],
                [
                    dla_m.higher,
                    dla_m.lower,
                    0,
                ],
            )
            * WEEKS_IN_YEAR
        )
