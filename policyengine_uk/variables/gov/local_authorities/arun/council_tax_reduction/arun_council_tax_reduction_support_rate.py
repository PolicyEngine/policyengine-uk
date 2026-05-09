from policyengine_uk.model_api import *


class arun_council_tax_reduction_support_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Arun Council Tax Reduction support rate"
    definition_period = YEAR
    reference = "https://www.arun.gov.uk/council-tax-reduction/"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.arun.council_tax_reduction
        weekly_income = benunit("arun_council_tax_reduction_weekly_income", period)
        weekly_income_for_band = weekly_income + 1e-9
        banded_support_rate = ctr.income_band.amount.calc(weekly_income_for_band)
        relevant_income_based_benefit = benunit(
            "council_tax_reduction_relevant_income_based_benefit", period
        )
        return where(relevant_income_based_benefit, 1, banded_support_rate)
