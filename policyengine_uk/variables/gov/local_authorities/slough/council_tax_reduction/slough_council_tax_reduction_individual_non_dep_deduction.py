from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class slough_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Slough Council Tax Support individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.slough.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "slough_council_tax_reduction_is_local_scheme",
                period,
            )
        )
        claimant_or_partner = claimant_benunit & household_person("is_adult", period)
        claimant_exempt = household.any(
            claimant_or_partner
            & (
                household_person("is_blind", period)
                | (household_person("dla_sc", period) > 0)
                | (household_person("pip_dl", period) > 0)
                | (household_person("armed_forces_independence_payment", period) > 0)
            )
        )
        gross_earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        has_uc_award = person.benunit("universal_credit", period) > 0
        uc_no_earned_income = has_uc_award & (
            person("slough_council_tax_reduction_non_dep_uc_earned_income", period) <= 0
        )
        weekly_hours = person("weekly_hours", period)
        weekly_gross_earnings = gross_earned_income / WEEKS_IN_YEAR
        high_deduction = (
            ~uc_no_earned_income
            & (weekly_hours >= ctr.non_dep_deduction.work_hours)
            & (weekly_gross_earnings >= ctr.non_dep_deduction.earnings_threshold)
        )
        weekly_deduction = where(
            high_deduction,
            ctr.non_dep_deduction.high_amount,
            ctr.non_dep_deduction.low_amount,
        )
        full_time_student = is_full_time_student_non_dep(person, period)
        return local_scheme * where(
            claimant_exempt | full_time_student,
            0.0,
            weekly_deduction * WEEKS_IN_YEAR,
        )
