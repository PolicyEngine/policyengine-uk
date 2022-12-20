from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_or_higher import (
    LowerOrHigher,
)


class DLA_M_reported(Variable):
    value_type = float
    entity = Person
    label = "DLA (mobility) (reported)"
    definition_period = YEAR
    unit = GBP


class dla_m(Variable):
    label = "DLA (mobility)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        dla_m = parameters(period).gov.dwp.dla.mobility
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
