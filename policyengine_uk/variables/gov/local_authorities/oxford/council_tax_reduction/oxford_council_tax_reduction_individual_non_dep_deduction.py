from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_oxford_working_age,
)


class oxford_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Oxford CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.oxford.council_tax_reduction
        household = person.household
        working_age = is_oxford_working_age(
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
        claimant_exempt = person.household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        return working_age * where(
            claimant_exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR
        )
