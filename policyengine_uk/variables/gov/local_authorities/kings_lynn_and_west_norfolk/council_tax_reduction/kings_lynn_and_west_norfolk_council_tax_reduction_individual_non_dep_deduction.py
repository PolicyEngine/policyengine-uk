from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    earned_income_non_dep_deduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_kings_lynn_and_west_norfolk_working_age,
)


class kings_lynn_and_west_norfolk_council_tax_reduction_individual_non_dep_deduction(
    Variable
):
    value_type = float
    entity = Person
    label = "King's Lynn and West Norfolk CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.kings_lynn_and_west_norfolk.council_tax_reduction
        household = person.household
        working_age = is_kings_lynn_and_west_norfolk_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        return earned_income_non_dep_deduction(person, period, ctr, working_age)
