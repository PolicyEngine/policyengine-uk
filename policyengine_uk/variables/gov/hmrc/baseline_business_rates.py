from policyengine_uk.model_api import *


class baseline_business_rates(Variable):
    label = "Baseline business rates incidence"
    documentation = (
        "Total incidence from business rates exposure in the baseline"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        br = parameters(period).gov.hmrc.business_rates.statistics.revenue
        total_revenue = (
            br.ENGLAND  # HMRC
            + br.SCOTLAND  # Revenue Scotland
            + br.WALES  # Welsh Revenue Authority
            + br.NORTHERN_IRELAND  # HMRC
        )
        return household("shareholding", period) * total_revenue
