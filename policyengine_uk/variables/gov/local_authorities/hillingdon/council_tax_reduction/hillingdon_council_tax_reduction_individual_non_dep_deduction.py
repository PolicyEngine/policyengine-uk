from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_hillingdon_working_age,
)


class hillingdon_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Hillingdon CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.hillingdon.council_tax_reduction
        household = person.household
        working_age = is_hillingdon_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        state_pension_credit_age = person("is_SP_age", period)
        state_pension_credit = person.benunit("pension_credit", period) > 0
        exempt = (
            is_full_time_student_non_dep(person, period)
            | state_pension_credit_age
            | state_pension_credit
        )
        deduction = ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
        return working_age * where(exempt, 0.0, deduction)
