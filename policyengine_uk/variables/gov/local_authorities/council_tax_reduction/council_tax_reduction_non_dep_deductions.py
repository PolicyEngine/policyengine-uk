from policyengine_uk.model_api import *


class council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "CTR non-dependent deductions"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        deductions = benunit.members(
            "council_tax_reduction_individual_non_dep_deduction", period
        )
        deductions_in_household = benunit.max(benunit.members.household.sum(deductions))
        deductions_in_benunit = benunit.sum(deductions)
        return deductions_in_household - deductions_in_benunit
