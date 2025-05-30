from policyengine_uk.model_api import *


class dla_sc(Variable):
    label = "DLA (self-care)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        dla_sc = parameters(period).gov.dwp.dla.self_care
        category = person("dla_sc_category", period)
        categories = category.possible_values
        return (
            select(
                [
                    category == categories.HIGHER,
                    category == categories.MIDDLE,
                    category == categories.LOWER,
                    category == categories.NONE,
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
