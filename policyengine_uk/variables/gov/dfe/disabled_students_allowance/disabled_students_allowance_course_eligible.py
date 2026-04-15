from policyengine_uk.model_api import *


class disabled_students_allowance_course_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Course is eligible for Disabled Students' Allowance"
    documentation = (
        "Whether the person's course is eligible for Disabled Students' Allowance. "
        "This can be set explicitly in simulations. By default, the model uses the "
        "existing higher-education evidence proxy from the maintenance-loan model."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("maintenance_loan_in_higher_education", period)
