from policyengine_uk.model_api import *


class ealing_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Ealing CTR non-dependent deductions"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        deductions = benunit.members(
            "ealing_council_tax_reduction_individual_non_dep_deduction",
            period,
        )
        deductions_in_household = benunit.max(benunit.members.household.sum(deductions))
        return deductions_in_household - benunit.sum(deductions)
