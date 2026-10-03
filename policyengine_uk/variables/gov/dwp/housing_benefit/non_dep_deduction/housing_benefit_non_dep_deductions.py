from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.housing_benefit.non_dep_deduction._non_dependants import (
    charged_to_other_families,
    deduction_per_family,
)


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    documentation = (
        "Deductions for the non-dependants in other benefit units of the "
        "household: one for each couple, the higher of the two members' "
        "amounts, and one for each other member; none if the claimant or "
        "partner is exempt."
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
        deduction_for_benunit = deduction_per_family(benunit, period, deductions, False)
        claimant_exempt = benunit(
            "housing_benefit_non_dep_deductions_claimant_exempt", period
        )
        return where(
            claimant_exempt,
            0,
            charged_to_other_families(benunit, period, deduction_for_benunit),
        )
