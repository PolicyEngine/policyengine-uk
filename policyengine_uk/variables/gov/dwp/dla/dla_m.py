from policyengine_uk.model_api import *


class dla_m(Variable):
    label = "DLA (mobility)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        dla_m = parameters(period).gov.dwp.dla.mobility
        category = person("dla_m_category", period)
        categories = category.possible_values
        return (
            select(
                [
                    category == categories.HIGHER,
                    category == categories.LOWER,
                    category == categories.NONE,
                ],
                [
                    dla_m.higher,
                    dla_m.lower,
                    0,
                ],
            )
            * WEEKS_IN_YEAR
        )
