from policyengine_uk.model_api import *


class barking_and_dagenham_council_tax_reduction_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Barking and Dagenham CTS non-dependent deductions"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        deductions = benunit.members(
            "barking_and_dagenham_council_tax_reduction_individual_non_dep_deduction",
            period,
        )
        deductions_in_household = benunit.max(benunit.members.household.sum(deductions))
        return deductions_in_household - benunit.sum(deductions)
