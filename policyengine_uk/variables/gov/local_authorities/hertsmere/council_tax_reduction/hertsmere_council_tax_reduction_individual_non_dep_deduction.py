from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
    normal_gross_income_non_dep_deduction,
)


class hertsmere_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Hertsmere Council Tax Reduction individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.hertsmere.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "hertsmere_council_tax_reduction_is_local_scheme", period
            )
        )
        uc_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "hertsmere_council_tax_reduction_is_uc_scheme", period
            )
        )
        protected = household.any(
            claimant_benunit
            & household_person.benunit(
                "hertsmere_council_tax_reduction_protected_group", period
            )
        )
        non_uc_deduction = normal_gross_income_non_dep_deduction(
            person,
            period,
            ctr,
            local_scheme,
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
        weekly_hours = person.benunit.max(person("weekly_hours", period))
        in_remunerative_work = (
            weekly_hours >= ctr.non_dep_deduction.remunerative_work_hours
        )
        protected_weekly_amount = where(
            in_remunerative_work,
            ctr.uc_banded_scheme.protected_non_dep_deduction.amount.calc(
                weekly_benunit_gross_income
            ),
            ctr.uc_banded_scheme.protected_non_dep_deduction.amount.calc(0),
        )
        non_protected_weekly_amount = where(
            in_remunerative_work,
            ctr.uc_banded_scheme.non_protected_non_dep_deduction.amount.calc(
                weekly_benunit_gross_income
            ),
            ctr.uc_banded_scheme.non_protected_non_dep_deduction.amount.calc(0),
        )
        weekly_amount = where(
            protected, protected_weekly_amount, non_protected_weekly_amount
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
        has_uc = person.benunit("universal_credit", period) > 0
        uc_working_less_than_16_hours = (
            has_uc
            & (weekly_benunit_earned_income > 0)
            & (weekly_hours < ctr.non_dep_deduction.remunerative_work_hours)
        )
        exempt = (
            claimant_exempt
            | is_full_time_student_non_dep(person, period)
            | income_based_benefit
            | uc_working_less_than_16_hours
        )
        uc_deduction = local_scheme * where(exempt, 0, weekly_amount * WEEKS_IN_YEAR)
        return where(uc_scheme, uc_deduction, non_uc_deduction)
