from policyengine_uk.model_api import *


class dla_m(Variable):
    label = "DLA (mobility)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/1992/4/section/73",
        "https://www.legislation.gov.uk/ukpga/1992/7/section/73",
    )

    def formula(person, period, parameters):
        dla_m = parameters(period).gov.dwp.dla.mobility
        category = person("dla_m_category", period)
        categories = category.possible_values
        age = person("age", period)
        return (
            select(
                [
                    (category == categories.HIGHER) & (age >= dla_m.higher_min_age),
                    (category == categories.LOWER) & (age >= dla_m.lower_min_age),
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
