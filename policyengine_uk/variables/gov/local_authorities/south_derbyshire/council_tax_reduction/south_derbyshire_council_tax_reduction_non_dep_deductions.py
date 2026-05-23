from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "South Derbyshire Council Tax Reduction non-dependant deductions"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        deductions = benunit.members(
            "south_derbyshire_council_tax_reduction_individual_non_dep_deduction",
            period,
        )
        deduction_for_benunit = benunit.sum(deductions)
        is_benunit_head = benunit.members("is_benunit_head", period)
        deductions_to_count = is_benunit_head * benunit.project(deduction_for_benunit)
        deductions_in_household = benunit.max(
            benunit.members.household.sum(deductions_to_count)
        )
        return deductions_in_household - deduction_for_benunit
