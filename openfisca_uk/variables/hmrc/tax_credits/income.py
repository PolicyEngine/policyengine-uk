from openfisca_uk.model_api import *


class tax_credits_applicable_income(Variable):
    label = "Income for Tax Credits"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2006/regulation/3"

    def formula(benunit, period, parameters):
        tc = parameters(period).hmrc.tax_credits.means_test
        unearned_income = max_(
            0,
            aggr(benunit, period, tc.income.unearned.components)
            - tc.income.unearned.disregard,
        )
        earned_income = aggr(benunit, period, tc.income.earned)
        bi = parameters(period).contrib.ubi_center.basic_income
        if bi.include_in_means_tests:
            earned_income += benunit("basic_income", period)
        return unearned_income + earned_income


class tax_credits_reduction(Variable):
    label = "Label"
    documentation = "Description"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        wtc = benunit("maximum_wtc", period)
        ctc = benunit("maximum_ctc", period)
        entitlement = wtc + ctc
        income = benunit("tax_credits_applicable_income", period)
        means_test = parameters(period).hmrc.tax_credits.means_test
        threshold = where(
            wtc > 0, means_test.threshold.wtc, means_test.threshold.ctc
        )
        income_over_threshold = max_(0, income - threshold)
        reduction = means_test.reduction_rate * income_over_threshold
        return min_(reduction, entitlement)
