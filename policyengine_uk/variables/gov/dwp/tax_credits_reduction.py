from policyengine_uk.model_api import *


class tax_credits_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Reduction in Tax Credits from means-tested income"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        means_test = parameters(period).gov.dwp.tax_credits.means_test
        CTC_amount = benunit("CTC_maximum_rate", period)
        WTC_amount = benunit("WTC_maximum_rate", period)
        CTC_only = (CTC_amount > 0) & (WTC_amount == 0)
        threshold = where(
            CTC_only,
            means_test.income_threshold_CTC_only,
            means_test.income_threshold,
        )
        income = benunit("tax_credits_applicable_income", period)
        overage = max_(0, income - threshold)
        return overage * means_test.income_reduction_rate
