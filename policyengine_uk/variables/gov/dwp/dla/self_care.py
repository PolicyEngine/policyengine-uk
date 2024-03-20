from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_middle_or_higher import (
    LowerMiddleOrHigher,
)


class DLA_SC_reported(Variable):
    value_type = float
    entity = Person
    label = "DLA (self-care) (reported)"
    definition_period = YEAR
    unit = GBP


class dla_sc(Variable):
    label = "DLA (self-care)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        dla_sc = parameters(period).gov.dwp.dla.self_care
        category = person("dla_sc_category", period)
        return (
            select(
                [
                    category == LowerMiddleOrHigher.HIGHER,
                    category == LowerMiddleOrHigher.MIDDLE,
                    category == LowerMiddleOrHigher.LOWER,
                    category == LowerMiddleOrHigher.NONE,
                ],
                [
                    dla_sc.higher,
                    dla_sc.middle,
                    dla_sc.lower,
                    0,
                ],
            )
            * WEEKS_IN_YEAR
        )


class dla_sc_middle_plus(Variable):
    value_type = bool
    entity = Person
    label = "Receives at least middle-rate DLA (self-care)"
    definition_period = YEAR

    def formula(person, period, parameters):
        return is_in(
            person("dla_sc_category", period),
            [LowerMiddleOrHigher.MIDDLE, LowerMiddleOrHigher.HIGHER],
        )


class receives_highest_dla_sc(Variable):
    label = "Receives the highest DLA (self-care) category"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        return person("dla_sc_category", period) == LowerMiddleOrHigher.HIGHER
