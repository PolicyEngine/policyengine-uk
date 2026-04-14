from policyengine_uk.model_api import *


class childcare_grant_student_finance_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Eligible for income-assessed student finance for Childcare Grant"
    documentation = (
        "Whether the person gets, or is eligible for, income-assessed undergraduate student finance "
        "for Childcare Grant purposes. This can be set explicitly in simulations. By default it uses "
        "the maintenance loan eligibility proxy. Full-time status is modeled separately."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("maintenance_loan_eligible", period)
