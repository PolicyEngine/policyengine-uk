from policyengine_uk.model_api import *


class vat(Variable):
    label = "VAT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        full_rate_consumption = household("full_rate_vat_consumption", period)
        reduced_rate_consumption = household(
            "reduced_rate_vat_consumption", period
        )
        vat = parameters(period).gov.hmrc.vat
        return (
            full_rate_consumption * vat.standard_rate
            + reduced_rate_consumption * vat.reduced_rate
        )


class baseline_vat(Variable):
    label = "baseline VAT"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        full_rate_consumption = household("full_rate_vat_consumption", period)
        reduced_rate_consumption = household(
            "reduced_rate_vat_consumption", period
        )
        vat = parameters(period).baseline.gov.hmrc.vat
        return (
            full_rate_consumption * vat.standard_rate
            + reduced_rate_consumption * vat.reduced_rate
        )


class vat_change(Variable):
    label = "change in VAT liability"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    adds = ["vat"]
    subtracts = ["baseline_vat"]
