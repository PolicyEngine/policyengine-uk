from policyengine_uk.model_api import *


class uc_non_dep_deduction_exempt(Variable):
    value_type = bool
    entity = Person
    label = "Exempt from the Universal Credit non-dependent housing costs contributions deduction"
    definition_period = YEAR
    documentation = (
        "No housing costs contribution is deducted for a non-dependant who is "
        "receiving Pension Credit, the middle or higher rate of the DLA care "
        "component, the PIP daily living component or Attendance Allowance, or "
        "who is entitled to Carer's Allowance (underlying entitlement included, "
        "so the carer test is is_carer_for_benefits rather than receipt)."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/16"

    def formula(person, period, parameters):
        return (
            (person.benunit("pension_credit", period) > 0)
            | person("dla_sc_middle_plus", period)
            | (person("pip_dl", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | person("is_carer_for_benefits", period)
        )
