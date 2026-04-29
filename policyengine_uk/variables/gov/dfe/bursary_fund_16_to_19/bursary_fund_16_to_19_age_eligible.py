from policyengine_uk.model_api import *


class bursary_fund_16_to_19_age_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Age eligible for 16 to 19 Bursary Fund"
    documentation = "Whether the student is age eligible for the vulnerable-group 16 to 19 Bursary Fund."
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.bursary_fund_16_to_19.age
        age = person("age", period)
        return (age >= p.minimum) & (age < p.standard_upper)
