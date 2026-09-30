from policyengine_uk.model_api import *


class uc_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income (after disregards and tax)"
    definition_period = YEAR
    unit = GBP

    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/22"

    def formula(benunit, period, parameters):
        # Only the claimant's (or joint claimants') earned income counts
        # (UC Regs 2013 reg 22(1)(b)), with their own tax and pension
        # contributions deducted.
        personal_gross_earned_income = add_for_claimant_and_partner(
            benunit, period, ["uc_mif_capped_earned_income"]
        )
        disregards = add_for_claimant_and_partner(
            benunit,
            period,
            ["uc_work_allowance", "tax", "pension_contributions"],
        )
        return max_(0, personal_gross_earned_income - disregards)
