from openfisca_uk.model_api import *


class maximum_ctc(Variable):
    label = "CTC maximum rate"
    documentation = "The Child Tax Credit entitlement, before means-testing"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        allowed = parameters(
            period
        ).hmrc.tax_credits.child_tax_credit.elements.allowed
        total = sum([benunit(element, period) for element in allowed])
        eligible = benunit("is_ctc_eligible", period)
        return eligible * total


class ctc_reduction(Variable):
    label = "Child Tax Credit reduction"
    documentation = "The reduction in CTC entitlement due to the means test"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2008/regulation/8"

    def formula(benunit, period, parameters):
        means_test = parameters(period).hmrc.tax_credits.means_test
        wtc = benunit("wtc_pre_minimum", period)
        wtc_eliminating_income = wtc / means_test.reduction_rate
        threshold = means_test.threshold.ctc - wtc_eliminating_income
        income = benunit("tax_credits_applicable_income", period)
        income_over_threshold = max_(0, income - threshold)
        maximum_rate = benunit("maximum_ctc", period)
        reduction = means_test.reduction_rate * income_over_threshold
        return min_(maximum_rate, reduction)


class ctc_pre_minimum(Variable):
    label = "Child Tax Credit (before minimum benefit rules)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2008/regulation/8"

    def formula(benunit, period):
        maximum_rate = benunit("maximum_ctc", period)
        reduction = benunit("ctc_reduction", period)
        return maximum_rate - reduction


class child_tax_credit(Variable):
    label = "Child Tax Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2008/regulation/8"

    def formula(benunit, period):
        maximum_rate = benunit("ctc_pre_minimum", period)
        below_minimum = benunit("tax_credits_below_minimum", period)
        return maximum_rate * ~below_minimum * benunit("claims_ctc", period)
