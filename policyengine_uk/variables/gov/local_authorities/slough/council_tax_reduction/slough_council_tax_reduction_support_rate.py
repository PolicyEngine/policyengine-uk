from policyengine_uk.model_api import *


class slough_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Slough Council Tax Support rate"
    definition_period = YEAR
    reference = "https://www.slough.gov.uk/downloads/file/5730/council-tax-support-scheme-2026-27"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.slough.council_tax_reduction
        weekly_earnings = benunit(
            "slough_council_tax_reduction_weekly_earnings", period
        )
        no_earned_income = weekly_earnings <= 0
        earnings_band_rate = ctr.income_band.support_rate.calc(weekly_earnings)
        return where(
            no_earned_income,
            ctr.income_band.no_earned_income_support_rate,
            earnings_band_rate,
        )
