from policyengine_uk.model_api import *


class baseline_business_rates(Variable):
    label = "Baseline business rates incidence"
    documentation = "Total incidence from business rates exposure in the baseline"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        br = parameters(period).gov.hmrc.business_rates.statistics.revenue
        total_revenue = (
            br.ENGLAND  # Local rating lists, collected by councils
            + br.ENGLAND_CENTRAL_LIST  # Paid to the Secretary of State
            + br.SCOTLAND  # Collected by councils
            + br.WALES  # Local rating lists, collected by councils
            + br.WALES_CENTRAL_LIST  # Paid to the Welsh Government
            + br.NORTHERN_IRELAND  # Collected by Land & Property Services
        )
        return household("shareholding", period) * total_revenue
