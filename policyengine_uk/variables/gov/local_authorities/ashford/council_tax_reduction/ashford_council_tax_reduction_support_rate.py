from policyengine_uk.model_api import *


class ashford_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Ashford Council Tax Reduction support rate"
    definition_period = YEAR
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.ashford.council_tax_reduction
        weekly_income = benunit("ashford_council_tax_reduction_weekly_income", period)
        rounded_weekly_income = np.round(weekly_income * 100) / 100
        single_rate = ctr.income_band.single.calc(rounded_weekly_income + 1e-4)
        couple_rate = ctr.income_band.couple.calc(rounded_weekly_income + 1e-4)
        banded_support_rate = where(
            benunit("is_couple", period),
            couple_rate,
            single_rate,
        )
        passported = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(passported, 0.90, banded_support_rate)
