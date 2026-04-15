from policyengine_uk.model_api import *


class parents_learning_allowance_course_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Study-pattern eligible for Parents' Learning Allowance"
    documentation = (
        "Whether the person is on a course or study pattern that can qualify for Parents' Learning Allowance. "
        "This can be set explicitly in simulations. By default, the model proxies this from higher-education "
        "evidence rather than maintenance-loan eligibility, so England-specific finance rules are applied separately "
        "and simulations can still override the variable for 120-credit or teacher-training cases."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("maintenance_loan_in_higher_education", period)
