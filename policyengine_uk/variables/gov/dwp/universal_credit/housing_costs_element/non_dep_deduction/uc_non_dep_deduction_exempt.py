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
        "who receives Carer's Allowance or Carer Support Payment, or who is "
        "responsible for a child under the child responsibility age limit. "
        "Benefit-unit membership represents the child's normal residence "
        "with the claimant or partner; the existing Universal Credit child "
        "age measure excludes children looked after by a local authority. Underlying "
        "entitlement reduced to nil by overlapping benefits does not qualify "
        "for the carer exemption. Pension Credit is awarded to a benefit unit's claimant and partner, "
        "so another adult in the unit is not receiving it."
    )
    reference = "https://www.legislation.gov.uk/uksi/2013/376/schedule/4/paragraph/16"

    def formula(person, period, parameters):
        p = parameters(
            period
        ).gov.dwp.universal_credit.elements.housing.non_dep_deduction
        # Sch 4 para 16(2)(i) and reg 4: responsibility belongs to the
        # claimant or partner of the child's own family, independently of
        # whether that family claims Universal Credit.
        responsible_for_young_child = person("is_claimant_or_partner", period) & (
            person.benunit("uc_youngest_child_age", period)
            < p.child_responsibility_age_limit
        )
        return (
            # Pension Credit is the claimant's and partner's award, not that of
            # another adult in their benefit unit (para 16(2)(b)).
            (
                person("is_claimant_or_partner", period)
                & person.benunit("uc_non_dep_receives_pension_credit", period)
            )
            | person("dla_sc_middle_plus", period)
            | (person("pip_dl", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | person("receives_carer_benefit", period)
            | responsible_for_young_child
        )
