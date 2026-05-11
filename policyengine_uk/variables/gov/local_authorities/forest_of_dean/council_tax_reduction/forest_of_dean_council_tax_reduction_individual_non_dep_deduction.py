from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    normal_gross_income_non_dep_deduction,
)


class forest_of_dean_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Forest of Dean individual Council Tax Support non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.forest_of_dean.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "forest_of_dean_council_tax_reduction_is_local_scheme", period
            )
        )
        return normal_gross_income_non_dep_deduction(person, period, ctr, local_scheme)
