from policyengine_uk.model_api import *


class adult_dependants_grant_adult_receives_student_finance(Variable):
    value_type = bool
    entity = Person
    label = "Dependant adult receives student finance for Adult Dependants' Grant"
    documentation = (
        "Whether the dependant adult receives student finance, which makes the student ineligible for Adult Dependants' Grant. "
        "By default, this only detects another higher-education student within the same benefit unit; "
        "simulations can set it explicitly for harder-to-observe cases."
    )
    definition_period = YEAR
    default_value = False
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        he_members = person.benunit.sum(
            person.benunit.members("maintenance_loan_in_higher_education", period)
        )
        own_he = person("maintenance_loan_in_higher_education", period)
        return he_members - own_he > 0
