from policyengine_uk.model_api import *


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    documentation = (
        "Deductions for the non-dependants in other benefit units of the "
        "household: one per couple, the higher of the two members' amounts, "
        "and none if the claimant or partner is exempt."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/74",
        "https://www.legislation.gov.uk/uksi/2006/214/regulation/55",
    )

    def formula(benunit, period, parameters):
        deductions = benunit.members(
            "household_benefits_individual_non_dep_deduction", period
        )
        deduction_for_benunit = benunit.max(deductions)
        is_benunit_head = benunit.members("is_benunit_head", period)
        counted = is_benunit_head * benunit.project(deduction_for_benunit)
        deductions_in_household = benunit.max(benunit.members.household.sum(counted))
        claimant_exempt = benunit(
            "housing_benefit_non_dep_deductions_claimant_exempt", period
        )
        return where(
            claimant_exempt, 0, deductions_in_household - deduction_for_benunit
        )
