from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_sefton_working_age,
)


class sefton_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Sefton CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.sefton.council_tax_reduction
        household = person.household
        working_age = is_sefton_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        weekly_earned_income = person.benunit.sum(earned_income) / WEEKS_IN_YEAR
        in_remunerative_work = (
            person("weekly_hours", period)
            >= ctr.non_dep_deduction.remunerative_work_hours
        )
        weekly_gross_income = (
            person.benunit.sum(person("total_income", period)) / WEEKS_IN_YEAR
        )
        weekly_deduction = where(
            in_remunerative_work,
            ctr.non_dep_deduction.amount.calc(weekly_gross_income),
            ctr.non_dep_deduction.amount.calc(0),
        )
        claimant_exempt = person.household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        income_based_benefit = (
            (person.benunit("income_support", period) > 0)
            | (person.benunit("jsa_income", period) > 0)
            | (person.benunit("esa_income", period) > 0)
            | (person.benunit("pension_credit", period) > 0)
        )
        uc_exempt = (person.benunit("universal_credit", period) > 0) & (
            weekly_earned_income <= 0
        )
        exempt = claimant_exempt | income_based_benefit | uc_exempt
        return working_age * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)
