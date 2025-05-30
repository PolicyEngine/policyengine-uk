from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_middle_or_higher import (

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
