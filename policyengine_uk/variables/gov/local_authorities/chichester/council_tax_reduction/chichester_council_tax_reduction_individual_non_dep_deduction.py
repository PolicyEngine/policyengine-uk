from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    earned_income_non_dep_deduction,
    is_full_time_student_non_dep,
)


class chichester_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Chichester Council Tax Reduction individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.chichester.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "chichester_council_tax_reduction_is_local_scheme", period
            )
        )
        claimant_has_uc_award = household.any(
            claimant_benunit
            & (
                max_(
                    household_person.benunit(
                        "universal_credit_pre_benefit_cap", period
                    ),
                    household_person.benunit("universal_credit", period),
                )
                > 0
            )
        )
        non_uc_deduction = earned_income_non_dep_deduction(
            person,
            period,
            ctr,
            local_scheme,
            exempt_uc_no_earned_income=True,
            exempt_income_based_benefits=True,
        )
        benunit_weekly_hours = person.benunit.max(person("weekly_hours", period))
        in_remunerative_work = (person("age", period) >= 18) & (
            benunit_weekly_hours >= ctr.non_dep_deduction.remunerative_work_hours
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        exempt = (
            claimant_exempt
            | is_full_time_student_non_dep(person, period)
            | income_based_benefit
        )
        uc_deduction = where(
            exempt,
            0.0,
            in_remunerative_work * ctr.non_dep_deduction.uc_amount * WEEKS_IN_YEAR,
        )
        return where(claimant_has_uc_award, uc_deduction, non_uc_deduction)
