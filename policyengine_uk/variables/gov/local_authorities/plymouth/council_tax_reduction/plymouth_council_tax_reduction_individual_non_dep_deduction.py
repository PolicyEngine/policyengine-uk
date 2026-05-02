from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class plymouth_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Plymouth Council Tax Support individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.plymouth.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "plymouth_council_tax_reduction_is_local_scheme", period
            )
        )
        claimant_or_partner = claimant_benunit & household_person("is_adult", period)
        claimant_exempt = household.any(
            claimant_or_partner
            & (
                household_person("is_blind", period)
                | (household_person("attendance_allowance", period) > 0)
                | (household_person("dla_sc", period) > 0)
                | (household_person("pip_dl", period) > 0)
                | (household_person("armed_forces_independence_payment", period) > 0)
            )
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        has_uc_award = person.benunit("universal_credit", period) > 0
        uc_no_earned_income = has_uc_award & (
            person("plymouth_council_tax_reduction_non_dep_uc_earned_income", period)
            <= 0
        )
        full_time_student = is_full_time_student_non_dep(person, period)
        source_exemption = person(
            "plymouth_council_tax_reduction_non_dep_source_exemption", period
        )
        exempt = (
            claimant_exempt
            | full_time_student
            | income_based_benefit
            | uc_no_earned_income
            | source_exemption
        )
        return local_scheme * where(
            exempt, 0.0, ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
        )
