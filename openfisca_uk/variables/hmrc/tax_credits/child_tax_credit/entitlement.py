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
        tax_credits_reduction = benunit("tax_credits_reduction", period)
        wtc_reduction = benunit("wtc_reduction", period)
        ctc = benunit("maximum_ctc", period)
        return min_(tax_credits_reduction - wtc_reduction, ctc)


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


class ctc_pre_takeup(Variable):
    label = "Child Tax Credit entitlement, before take-up imputations."
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2008/regulation/8"

    def formula(benunit, period, parameters):
        maximum_rate = benunit("ctc_pre_minimum", period)
        below_minimum = benunit("tax_credits_below_minimum", period)
        return maximum_rate * ~below_minimum


class child_tax_credit(Variable):
    label = "Child Tax Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2008/regulation/8"

    def formula(benunit, period, parameters):
        return benunit("ctc_pre_takeup", period) * benunit(
            "claims_ctc", period
        )
