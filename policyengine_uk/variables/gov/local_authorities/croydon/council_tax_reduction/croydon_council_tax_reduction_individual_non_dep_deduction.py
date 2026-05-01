from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_croydon_working_age,
)


class croydon_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Croydon Council Tax Support individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.croydon.council_tax_reduction
        household = person.household
        working_age = is_croydon_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        benunit_earned_income = person.benunit.sum(earned_income)
        weekly_deduction = where(
            benunit_earned_income > 0,
            ctr.non_dep_deduction.working_amount.calc(benunit_earned_income),
            ctr.non_dep_deduction.not_working_amount,
        )
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        claimant_disabled_not_working = household.any(
            claimant_benunit
            & household_person.benunit(
                "croydon_council_tax_reduction_disabled_not_working", period
            )
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        full_time_student = is_full_time_student_non_dep(person, period)
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        exempt = (
            claimant_exempt
            | claimant_disabled_not_working
            | full_time_student
            | income_based_benefit
        )
        return working_age * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)
