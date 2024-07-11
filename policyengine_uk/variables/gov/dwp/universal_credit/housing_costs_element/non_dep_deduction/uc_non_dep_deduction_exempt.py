from policyengine_uk.model_api import *


class uc_non_dep_deduction_exempt(Variable):
    value_type = bool
    entity = Person
    label = "Exempt from the Universal Credit non-dependent housing costs contributions deduction"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            (person.benunit("pension_credit", period) > 0)
            | person("dla_sc_middle_plus", period)
            | (person("pip_dl", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | person("receives_carers_allowance", period)
        )
