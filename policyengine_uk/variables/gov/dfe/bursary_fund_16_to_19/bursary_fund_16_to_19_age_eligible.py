from policyengine_uk.model_api import *


class bursary_fund_16_to_19_age_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Age eligible for 16 to 19 Bursary Fund"
    documentation = (
        "Whether the student is age eligible for the 16 to 19 Bursary Fund, including the "
        "funded extension for certain students aged 19 to 24."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.bursary_fund_16_to_19.age
        age = person("age", period)
        funded_extension = person("bursary_fund_16_to_19_funded_extension", period)
        standard_age_eligible = (age >= p.minimum) & (age < p.standard_upper)
        extended_age_eligible = (
            funded_extension & (age >= p.minimum) & (age < p.extended_upper)
        )
        return standard_age_eligible | extended_age_eligible
