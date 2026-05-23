from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_north_norfolk_working_age,
)


class north_norfolk_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "North Norfolk CTR individual non-dependent deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"

    def formula(person, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.north_norfolk.council_tax_reduction
        household = person.household
        working_age = is_north_norfolk_working_age(
            household("local_authority", period),
            household("country", period),
            household("council_tax_reduction_household_has_pensioner", period),
        )
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        claimant_or_partner = claimant_benunit & household_person("is_adult", period)
        claimant_limited_capability = household.any(
            claimant_or_partner
            & household_person("uc_limited_capability_for_WRA", period)
        )
        claimant_exempt = (
            household("council_tax_reduction_household_has_non_dep_exemption", period)
            | claimant_limited_capability
        )
        deduction = ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
        return working_age * where(claimant_exempt, 0.0, deduction)
