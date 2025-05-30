from policyengine_uk.model_api import *


class is_child_or_QYP(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a child or qualifying young person for most benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period) < 16) | person("is_QYP", period)
