from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_ealing_working_age,
)


class ealing_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Ealing CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.ealing.council_tax_reduction
        household = person.household
        working_age = is_ealing_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        claimant_exempt = household(
            "council_tax_reduction_household_has_non_dep_exemption", period
        )
        gross_earnings = person("employment_income", period) + person(
            "self_employment_income", period
        )
        weekly_gross_earnings = gross_earnings / WEEKS_IN_YEAR
        exempt = claimant_exempt | is_full_time_student_non_dep(person, period)
        deduction = (
            ctr.non_dep_deduction.amount.calc(weekly_gross_earnings) * WEEKS_IN_YEAR
        )
        return working_age * where(exempt, 0.0, deduction)
