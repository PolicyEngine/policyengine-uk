from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_islington_working_age,
)


class islington_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Islington CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.islington.council_tax_reduction
        household = person.household
        working_age = is_islington_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        weekly_benunit_earned_income = person.benunit.sum(earned_income) / WEEKS_IN_YEAR
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        universal_credit_no_earnings = (
            person.benunit("universal_credit", period) > 0
        ) & (weekly_benunit_earned_income <= 0)
        exempt = (
            is_full_time_student_non_dep(person, period)
            | income_based_benefit
            | universal_credit_no_earnings
        )
        deduction = ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
        return working_age * where(exempt, 0.0, deduction)
