from policyengine_uk.model_api import *


class housing_benefit_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "non-dependent deductions"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        deductions = benunit.members(
            "household_benefits_individual_non_dep_deduction", period
        )
        non_dep_deductions_in_hh = benunit.max(
            benunit.members.household.sum(deductions)
        )
        non_dep_deductions_in_bu = benunit.sum(deductions)
        return non_dep_deductions_in_hh - non_dep_deductions_in_bu
