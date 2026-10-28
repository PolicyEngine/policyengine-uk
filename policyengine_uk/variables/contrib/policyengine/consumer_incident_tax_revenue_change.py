from policyengine_uk.model_api import *


class consumer_incident_tax_revenue_change(Variable):
    label = "consumer-incident tax revenue change"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        consumption = household("consumption", period)
        share = consumption / 846e9
        if household.simulation.dataset is not None:
            weight = household("household_weight", period)
            weighted_total = (consumption * weight).sum()
            if weighted_total != 0:
                share = consumption / weighted_total
        revenue_change = parameters(
            period
        ).gov.contrib.policyengine.budget.consumer_incident_tax_change
        return revenue_change * share * 1e9
