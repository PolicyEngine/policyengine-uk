from policyengine_uk.model_api import *


class uc_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit non-dependent deductions"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        # Deductions are made for non-dependents outside the benefit unit,
        # but within the household, who meet certain conditions. To do this,
        # we first calculate the non-dependent deduction for each person (from
        # the perspective of a different benefit unit). Then, to calculate
        # the deduction for non-dependents outside the benefit unit, we subtract
        # the total non-dependent deductions for the benefit unit members from
        # the deductions for household members.
        deductions = benunit.members("uc_individual_non_dep_deduction", period)
        non_dep_deductions_in_hh = benunit.max(
            benunit.members.household.sum(deductions)
        )
        non_dep_deductions_in_bu = benunit.sum(deductions)
        return non_dep_deductions_in_hh - non_dep_deductions_in_bu
