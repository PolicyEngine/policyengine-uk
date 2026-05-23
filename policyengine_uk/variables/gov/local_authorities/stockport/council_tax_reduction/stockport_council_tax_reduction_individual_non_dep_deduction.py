from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_stockport_working_age,
)


class stockport_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Stockport CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.stockport.council_tax_reduction
        gross_income = add(
            person,
            period,
            [
                "employment_income",
                "self_employment_income",
                "property_income",
                "private_pension_income",
                "savings_interest_income",
                "dividend_income",
                "state_pension",
            ],
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        weekly_benunit_gross_income = person.benunit.sum(gross_income) / WEEKS_IN_YEAR
        weekly_benunit_earned_income = person.benunit.sum(earned_income) / WEEKS_IN_YEAR
        weekly_deduction = ctr.non_dep_deduction.amount.calc(
            weekly_benunit_gross_income
        )
        household = person.household
        working_age = is_stockport_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
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
        uc_no_earned_income = (person.benunit("universal_credit", period) > 0) & (
            weekly_benunit_earned_income <= 0
        )
        exempt = (
            claimant_exempt
            | full_time_student
            | income_based_benefit
            | uc_no_earned_income
        )
        return working_age * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)
