from policyengine_uk.model_api import *


class maintenance_loan_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible for maintenance loan"
    documentation = (
        "Whether the person is eligible for the maintenance loan model. "
        "This can be set explicitly in simulations. By default, the model requires "
        "the England maintenance-loan system, age 18+, and explicit higher-education evidence "
        "rather than the age-based current_education fallback."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        in_england = person("maintenance_loan_in_england_system", period)
        age = person("age", period)
        higher_education = person("maintenance_loan_in_higher_education", period)
        return in_england & (age >= 18) & higher_education
