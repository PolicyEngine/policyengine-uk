from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_brent_working_age,
)


class brent_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Brent Council Tax Support individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.brent.council_tax_reduction
        household = person.household
        working_age = is_brent_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        earned_income = person("employment_income", period) + person(
            "self_employment_income", period
        )
        working = earned_income > 0
        weekly_deduction = where(
            working,
            ctr.non_dep_deduction.working_amount,
            ctr.non_dep_deduction.not_working_amount,
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        full_time_student = is_full_time_student_non_dep(person, period)
        return (
            working_age
            * where(claimant_exempt | full_time_student, 0.0, weekly_deduction)
            * WEEKS_IN_YEAR
        )
