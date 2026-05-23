from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class north_northamptonshire_council_tax_reduction_individual_non_dep_deduction(
    Variable
):
    value_type = float
    entity = Person
    label = (
        "North Northamptonshire Council Tax Support individual non-dependant deduction"
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.north_northamptonshire.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "north_northamptonshire_council_tax_reduction_is_local_scheme",
                period,
            )
        )
        gross_income_components = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "private_pension_income",
            "savings_interest_income",
            "dividend_income",
            "social_security_income",
        ]
        person_gross_income = add(person, period, gross_income_components)
        benunit_gross_income = person.benunit.sum(person_gross_income) + add(
            person.benunit,
            period,
            ["child_benefit", "tax_credits", "universal_credit"],
        )
        has_uc_award = person.benunit("universal_credit", period) > 0
        gross_income = where(has_uc_award, person_gross_income, benunit_gross_income)
        weekly_gross_income = gross_income / WEEKS_IN_YEAR
        weekly_hours = where(
            has_uc_award,
            person("weekly_hours", period),
            person.benunit.max(person("weekly_hours", period)),
        )
        in_remunerative_work = (
            weekly_hours >= ctr.non_dep_deduction.remunerative_work_hours
        )
        weekly_deduction = where(
            in_remunerative_work,
            ctr.non_dep_deduction.amount.calc(weekly_gross_income),
            ctr.non_dep_deduction.amount.calc(0),
        )
        claimant_or_partner = claimant_benunit & household_person("is_adult", period)
        claimant_exempt = household.any(
            claimant_or_partner
            & (
                household_person("is_blind", period)
                | (household_person("attendance_allowance", period) > 0)
                | (household_person("armed_forces_independence_payment", period) > 0)
                | household_person(
                    "north_northamptonshire_council_tax_reduction_claimant_source_non_dep_exemption",
                    period,
                )
                | (household_person("dla_sc", period) > 0)
                | (household_person("pip_dl", period) > 0)
            )
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        uc_no_earned_income = has_uc_award & (
            person(
                "north_northamptonshire_council_tax_reduction_non_dep_uc_earned_income",
                period,
            )
            <= 0
        )
        exempt = (
            claimant_exempt
            | is_full_time_student_non_dep(person, period)
            | income_based_benefit
            | uc_no_earned_income
            | person(
                "north_northamptonshire_council_tax_reduction_non_dep_source_exemption",
                period,
            )
        )
        return local_scheme * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)
