from policyengine_uk.model_api import *


class is_QYP(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a qualifying young person for benefits purposes"
    definition_period = YEAR

    def formula(person, period, parameters):
        education = person("current_education", period)
        under_20 = person("age", period) < 20
        in_education = ~(
            education == education.possible_values.NOT_IN_EDUCATION
        )
        return under_20 & in_education
