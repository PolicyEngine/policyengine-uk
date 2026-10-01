from policyengine_uk.model_api import *


class uc_non_dep_deduction_exempt(Variable):
    value_type = bool
    entity = Person
    label = "Exempt from the Universal Credit non-dependent housing costs contributions deduction"
    definition_period = YEAR
    documentation = (
        "No housing costs contribution is deducted for a non-dependant who is "
        "receiving Pension Credit, the middle or higher rate of the DLA care "
        "component, the PIP daily living component or Attendance Allowance, "
        "who is entitled to Carer's Allowance (underlying entitlement "
        "included, so the carer test is is_carer_for_benefits rather than "
        "receipt), or who is responsible for a child under 5. Pension Credit "
        "is awarded to a benefit unit's claimant and partner, so another "
        "adult in the unit is not receiving it; likewise only the claimant "
        "and partner are responsible for the unit's children. The Scottish "
        "disability assistance limbs (Scottish adult DLA, pension age "
        "disability payment, adult disability payment), entitlement "
        "suspended in hospital, prisoners and armed forces members away on "
        "operations have no inputs and are not modelled."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/16"

    def formula(person, period, parameters):
        receives_pension_credit = person("is_claimant_or_partner", period) & (
            person.benunit("pension_credit", period) > 0
        )
        return (
            receives_pension_credit
            | person("dla_sc_middle_plus", period)
            | (person("pip_dl", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | person("is_carer_for_benefits", period)
            | person("is_responsible_for_child_under_5_for_universal_credit", period)
        )
