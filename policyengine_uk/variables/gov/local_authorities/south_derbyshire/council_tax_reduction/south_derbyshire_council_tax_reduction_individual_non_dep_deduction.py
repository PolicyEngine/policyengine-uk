from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction._legacy import (
    is_full_time_student_non_dep,
)


class south_derbyshire_council_tax_reduction_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "South Derbyshire Council Tax Reduction individual non-dependant deduction"
    definition_period = YEAR
    unit = GBP
    defined_for = "council_tax_reduction_individual_non_dep_deduction_eligible"
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"

    def formula(person, period, parameters):
        ctr = parameters(
            period
        ).gov.local_authorities.south_derbyshire.council_tax_reduction
        household = person.household
        household_person = household.members
        claimant_benunit = household_person.benunit(
            "benunit_contains_household_head", period
        )
        local_scheme = household.any(
            claimant_benunit
            & household_person.benunit(
                "south_derbyshire_council_tax_reduction_is_local_scheme",
                period,
            )
        )
        claimant_or_partner = claimant_benunit & household_person("is_adult", period)
        claimant_exempt = household.any(
            claimant_or_partner
            & (
                household_person("is_blind", period)
                | (household_person("attendance_allowance", period) > 0)
                | (household_person("armed_forces_independence_payment", period) > 0)
                | (household_person("dla_sc", period) > 0)
                | (household_person("pip_dl", period) > 0)
                | household_person(
                    "south_derbyshire_council_tax_reduction_claimant_source_non_dep_exemption",
                    period,
                )
            )
        )
        non_dep_exempt = is_full_time_student_non_dep(person, period) | person(
            "south_derbyshire_council_tax_reduction_non_dep_source_exemption",
            period,
        )
        deduction = ctr.non_dep_deduction.amount * WEEKS_IN_YEAR
        return local_scheme * where(claimant_exempt | non_dep_exempt, 0.0, deduction)
