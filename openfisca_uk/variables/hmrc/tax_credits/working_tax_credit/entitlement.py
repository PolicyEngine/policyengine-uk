from openfisca_uk.model_api import *


class maximum_wtc(Variable):
    label = "WTC maximum rate"
    documentation = "Working Tax Credit entitlement, before means-testing"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        allowed = parameters(
            period
        ).hmrc.tax_credits.working_tax_credit.elements.allowed
        total = sum(
            [benunit(f"wtc_{element}_element", period) for element in allowed]
        )
        eligible = benunit("is_wtc_eligible", period)
        return eligible * total


class wtc_reduction(Variable):
    label = "WTC reduction"
    documentation = "The reduction in WTC entitlement due to the means test"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2008/regulation/7"

    def formula(benunit, period, parameters):
        tax_credits_reduction = benunit("tax_credits_reduction", period)
        wtc = benunit("maximum_wtc", period)
        return min_(tax_credits_reduction, wtc)


class wtc_pre_minimum(Variable):
    label = "Working Tax Credit (before minimum benefit rules)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2008/regulation/7"

    def formula(benunit, period, parameters):
        maximum_rate = benunit("maximum_wtc", period)
        reduction = benunit("wtc_reduction", period)
        return maximum_rate - reduction


class wtc_pre_takeup(Variable):
    label = "Working Tax Credit"
    documentation = (
        "Working Tax Credit entitlement, before take-up imputations."
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2008/regulation/7"

    def formula(benunit, period, parameters):
        maximum_rate = benunit("wtc_pre_minimum", period)
        below_minimum = benunit("tax_credits_below_minimum", period)
        return maximum_rate * ~below_minimum


class working_tax_credit(Variable):
    label = "Working Tax Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    reference = "https://www.legislation.gov.uk/uksi/2002/2008/regulation/7"

    def formula(benunit, period, parameters):
        covid_payment = parameters(
            period
        ).hmrc.tax_credits.working_tax_credit.coronavirus_payment
        wtc = benunit("wtc_pre_takeup", period)
        increased_wtc = where(wtc > 0, wtc + covid_payment, wtc)
        return increased_wtc * benunit("claims_wtc", period)
