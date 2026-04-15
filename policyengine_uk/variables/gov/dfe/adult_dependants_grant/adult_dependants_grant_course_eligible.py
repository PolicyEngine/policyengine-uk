from policyengine_uk.model_api import *


class adult_dependants_grant_course_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Study-pattern eligible for Adult Dependants' Grant"
    documentation = (
        "Whether the person is on a course or study pattern that can qualify for Adult Dependants' Grant. "
        "This can be set explicitly in simulations. By default, the model proxies this from higher-education "
        "evidence rather than a narrower England-finance rule, so simulations can override the variable for "
        "full-time and teacher-training edge cases."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("maintenance_loan_in_higher_education", period)
