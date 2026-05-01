from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_bury_working_age,
)


class bury_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Bury CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.bury.council_tax_reduction
        household = person.household
        working_age = is_bury_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        uc_no_earned_income = (person.benunit("universal_credit", period) > 0) & (
            person.benunit.sum(earned_income) <= 0
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
                | (household_person("dla_sc", period) > 0)
                | (household_person("pip_dl", period) > 0)
                | (household_person("armed_forces_independence_payment", period) > 0)
            )
        )
        full_time_student = is_full_time_student_non_dep(person, period)
        exempt = (
            claimant_exempt
            | full_time_student
            | income_based_benefit
            | uc_no_earned_income
        )
        annual_deduction = ctr.non_dep_deduction.monthly_amount * MONTHS_IN_YEAR
        return working_age * where(exempt, 0.0, annual_deduction)
