from policyengine_uk.model_api import *


class westmorland_and_furness_council_tax_reduction_uc_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Westmorland and Furness Council Tax Reduction Universal Credit applicable income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.westmorlandandfurness.gov.uk/sites/default/files/2026-03/Westmorland%20%26%20Furness%20Council%20%20CTR%20Scheme%20202627%20%28accessible%20March%202026%29.pdf"

    def formula(benunit, period, parameters):
        has_uc_award = benunit("universal_credit", period) > 0
        uc_income = benunit("uc_earned_income", period) + benunit(
            "uc_unearned_income", period
        )
        uc_award = benunit("universal_credit", period)
        return has_uc_award * (uc_income + uc_award)
