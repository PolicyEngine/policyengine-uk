from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    normal_gross_income_non_dep_deduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_westminster_working_age,
)


class westminster_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Westminster CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(period).gov.local_authorities.westminster.council_tax_reduction
        household = person.household
        working_age = is_westminster_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        return normal_gross_income_non_dep_deduction(
            person,
            period,
            ctr,
            working_age,
            exempt_uc_no_earned_income=True,
        )
