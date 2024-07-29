from policyengine_uk.model_api import *

MICRODATA_VAT_COVERAGE = 0.38
"""
LCFS (from which ETB data is derived) microdata is known to under-report household consumption. We scale up the VAT liability to hit HMRC-reported VAT receipts (following the approach of IFS' TAXBEN, though they might have better coverage anyway from access to the non-EUL dataset).

For HMRC statistics see: https://www.gov.uk/government/statistics/value-added-tax-vat-annual-statistics
"""


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
        ) / MICRODATA_VAT_COVERAGE


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
        ) / MICRODATA_VAT_COVERAGE


class vat_change(Variable):
    label = "change in VAT liability"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    adds = ["vat"]
    subtracts = ["baseline_vat"]
