from policyengine_uk.model_api import *


class is_of_compulsory_school_age(Variable):
    value_type = bool
    entity = Person
    label = "Whether the person is of compulsory school age"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        p = parameters(period).gov.dfe
        return p.compulsory_school_age.calc(age)
