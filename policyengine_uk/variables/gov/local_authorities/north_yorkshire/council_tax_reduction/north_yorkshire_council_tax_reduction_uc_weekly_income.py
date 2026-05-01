from policyengine_uk.model_api import *


class north_yorkshire_council_tax_reduction_uc_weekly_income(Variable):
    value_type = float
    entity = BenUnit
    label = "North Yorkshire Council Tax Reduction weekly Universal Credit income"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.northyorks.gov.uk/sites/default/files/2026-03/North%20Yorkshire%20Council%27s%20Council%20Tax%20Reduction%20Scheme%202026%20to%202027.pdf"

    def formula(benunit, period, parameters):
        has_uc_award = benunit("universal_credit", period) > 0
        uc_income = benunit("uc_earned_income", period) + benunit(
            "uc_unearned_income", period
        )
        uc_award = benunit("universal_credit", period)
        uc_maximum_amount = benunit("uc_maximum_amount", period)
        housing_element = benunit("uc_housing_costs_element", period)
        housing_element_ratio = where(
            uc_maximum_amount > 0,
            min_(1, max_(0, uc_award / uc_maximum_amount)),
            0,
        )
        housing_element_disregard = min_(
            housing_element,
            housing_element * housing_element_ratio,
        )
        countable_uc_award = max_(
            0,
            uc_award - housing_element_disregard,
        )
        return has_uc_award * max_(0, uc_income + countable_uc_award) / WEEKS_IN_YEAR
