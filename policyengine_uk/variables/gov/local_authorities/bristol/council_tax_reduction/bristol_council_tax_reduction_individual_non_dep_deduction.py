from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_bristol_working_age,
)


class bristol_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Bristol Council Tax Reduction individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.bristol.council_tax_reduction
        household = person.household
        working_age = is_bristol_working_age(
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
            "social_security_income",
        ]
        person_gross_income = add(person, period, gross_income_components)
        person_earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        benunit_gross_income = person.benunit.sum(person_gross_income) + add(
            person.benunit,
            period,
            ["child_benefit", "tax_credits", "universal_credit"],
        )
        benunit_earned_income = person.benunit.sum(person_earned_income)
        income_for_table = where(
            person.benunit("is_couple", period),
            benunit_gross_income,
            benunit_earned_income,
        )
        weekly_income_for_table = income_for_table / WEEKS_IN_YEAR
        in_work = benunit_earned_income > 0
        weekly_deduction = where(
            in_work,
            ctr.non_dep_deduction.amount.calc(weekly_income_for_table),
            ctr.non_dep_deduction.amount.calc(0),
        )
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        claimant_or_partner = claimant_benunit & household_person("is_adult", period)
        claimant_exempt = household.any(
            claimant_or_partner
            & (
                household_person("is_blind", period)
                | (household_person("attendance_allowance", period) > 0)
                | (household_person("armed_forces_independence_payment", period) > 0)
                | household_person(
                    "bristol_council_tax_reduction_claimant_source_non_dep_exemption",
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
        uc_no_earned_income = (person.benunit("universal_credit", period) > 0) & (
            benunit_earned_income <= 0
        )
        exempt = (
            claimant_exempt
            | is_full_time_student_non_dep(person, period)
            | income_based_benefit
            | uc_no_earned_income
            | person("bristol_council_tax_reduction_non_dep_source_exemption", period)
        )
        return working_age * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)
