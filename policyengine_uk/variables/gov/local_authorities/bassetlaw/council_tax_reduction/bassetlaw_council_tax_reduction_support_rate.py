from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Bassetlaw Council Tax Reduction support rate"
    definition_period = YEAR
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.bassetlaw.council_tax_reduction
        weekly_income = benunit("bassetlaw_council_tax_reduction_weekly_income", period)
        rounded_weekly_income = np.round(weekly_income * 100) / 100
        banded_support_rate = ctr.income_band.support_rate.calc(
            rounded_weekly_income + 1e-4
        )
        vulnerable = (
            (benunit("severe_disability_premium", period) > 0)
            | benunit("bassetlaw_council_tax_reduction_sdp_transitional_award", period)
        )
        uc_award = max_(
            benunit("universal_credit_pre_benefit_cap", period),
            benunit("universal_credit", period),
        )
        maximum_uc = (uc_award > 0) & (
            uc_award >= benunit("uc_maximum_amount", period)
        )
        passported_band_2 = (
            benunit("council_tax_reduction_relevant_income_based_benefit", period)
            | maximum_uc
        )
        return select(
            [vulnerable, passported_band_2],
            [ctr.income_band.vulnerable_support_rate, 0.88],
            default=banded_support_rate,
        )
