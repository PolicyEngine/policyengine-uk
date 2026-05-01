from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_redbridge_working_age,
)


class redbridge_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Redbridge Council Tax Reduction individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.redbridge.council_tax_reduction
        household = person.household
        working_age = is_redbridge_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        statutory_pay = (
            person("statutory_sick_pay", period)
            + person("statutory_maternity_pay", period)
            + person("statutory_paternity_pay", period)
        )
        in_remunerative_work = (earned_income + statutory_pay) > 0
        weekly_deduction = where(
            in_remunerative_work,
            ctr.non_dep_deduction.working_amount,
            ctr.non_dep_deduction.not_working_amount,
        )
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        claimant_disability_class = household.any(
            claimant_benunit
            & household_person.benunit(
                "redbridge_council_tax_reduction_disability_class", period
            )
        )
        exempt = claimant_disability_class | (person("carers_allowance", period) > 0)
        return working_age * where(exempt, 0.0, weekly_deduction * WEEKS_IN_YEAR)
