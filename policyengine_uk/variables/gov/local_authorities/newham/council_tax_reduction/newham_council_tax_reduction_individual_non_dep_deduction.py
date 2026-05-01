from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_newham_working_age,
)


class newham_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Newham CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.newham.council_tax_reduction
        household = person.household
        working_age = is_newham_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        weekly_benunit_earnings = person.benunit.sum(earned_income) / WEEKS_IN_YEAR
        benunit_weekly_hours = person.benunit.max(person("weekly_hours", period))
        in_remunerative_work = (
            benunit_weekly_hours >= ctr.non_dep_deduction.remunerative_work_hours
        )
        weekly_deduction = where(
            in_remunerative_work,
            ctr.non_dep_deduction.amount.calc(weekly_benunit_earnings),
            ctr.non_dep_deduction.amount.calc(0),
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        has_uc = person.benunit("universal_credit", period) > 0
        no_earned_income = weekly_benunit_earnings <= 0
        claimant_exempt = person.household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        exempt = claimant_exempt | income_based_benefit | (has_uc & no_earned_income)
        return working_age * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)

