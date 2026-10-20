from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    normal_gross_income_non_dep_deduction,
)
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_kingston_upon_thames_area,
)


class kingston_upon_thames_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Kingston upon Thames CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.kingston_upon_thames.council_tax_reduction
        household = person.household
        # Each claimant's own scheme decides whether their award uses this.
        in_scheme_area = is_kingston_upon_thames_area(
            household("local_authority", period),
            household("country", period),
        )
        return normal_gross_income_non_dep_deduction(
            person,
            period,
            ctr,
            in_scheme_area,
            exempt_uc_no_earned_income=True,
        )
