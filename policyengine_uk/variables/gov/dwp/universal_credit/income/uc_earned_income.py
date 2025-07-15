from policyengine_uk.model_api import *


class uc_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income (after disregards and tax)"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        personal_gross_earned_income = add(
            benunit, period, ["uc_mif_capped_earned_income"]
        )
        disregards = add(
            benunit,
            period,
            ["uc_work_allowance", "benunit_tax", "pension_contributions"],
        )
        return max_(0, personal_gross_earned_income - disregards)
