from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_harrow_working_age,
)


class harrow_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Harrow CTS individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.harrow.council_tax_reduction
        household = person.household
        working_age = is_harrow_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        gross_income_components = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "private_pension_income",
            "savings_interest_income",
            "dividend_income",
            "state_pension",
        ]
        gross_income = add(person, period, gross_income_components)
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        weekly_benunit_gross_income = person.benunit.sum(gross_income) / WEEKS_IN_YEAR
        weekly_benunit_earned_income = person.benunit.sum(earned_income) / WEEKS_IN_YEAR
        benunit_weekly_hours = person.benunit.max(person("weekly_hours", period))
        remunerative_work = (
            benunit_weekly_hours >= ctr.non_dep_deduction.remunerative_work_hours
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        maximum_uc = (person.benunit("universal_credit", period) > 0) & (
            person.benunit("universal_credit", period)
            >= person.benunit("uc_maximum_amount", period)
        )
        legacy_weekly_deduction = where(
            income_based_benefit | maximum_uc,
            ctr.non_dep_deduction.legacy_income_based_amount,
            where(
                remunerative_work,
                ctr.non_dep_deduction.legacy_amount.calc(weekly_benunit_gross_income),
                ctr.non_dep_deduction.legacy_amount.calc(0),
            ),
        )
        uc_weekly_deduction = where(
            remunerative_work
            & (
                weekly_benunit_gross_income
                >= ctr.non_dep_deduction.uc_high_income_threshold
            ),
            ctr.non_dep_deduction.uc_high_amount,
            ctr.non_dep_deduction.uc_low_amount,
        )
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        household_head_has_uc = household.any(
            claimant_benunit
            & (household_person.benunit("universal_credit", period) > 0)
        )
        weekly_deduction = where(
            household_head_has_uc, uc_weekly_deduction, legacy_weekly_deduction
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        full_time_student = is_full_time_student_non_dep(person, period)
        exempt = claimant_exempt | full_time_student
        return working_age * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)
