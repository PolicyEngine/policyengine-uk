from policyengine_uk.model_api import *


class HB_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Non-dependent deductions"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        non_dep_deductions_in_hh = benunit.max(
            benunit.members.household.sum(
                benunit.members("HB_individual_non_dep_deduction", period)
            )
        )
        non_dep_deductions_in_bu = add(
            benunit, period, ["HB_individual_non_dep_deduction"]
        )
        return non_dep_deductions_in_hh - non_dep_deductions_in_bu
