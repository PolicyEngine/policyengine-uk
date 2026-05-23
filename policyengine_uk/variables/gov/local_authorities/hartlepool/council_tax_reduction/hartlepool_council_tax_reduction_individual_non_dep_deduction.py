from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class hartlepool_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Hartlepool individual Council Tax Reduction non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.hartlepool.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "hartlepool_council_tax_reduction_is_local_scheme", period
            )
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        uc_no_earned_income = (person.benunit("universal_credit", period) > 0) & (
            person.benunit.sum(earned_income) <= 0
        )
        exempt = (
            claimant_exempt
            | is_full_time_student_non_dep(person, period)
            | income_based_benefit
            | uc_no_earned_income
        )
        return local_scheme * where(
            exempt, 0, ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
        )
