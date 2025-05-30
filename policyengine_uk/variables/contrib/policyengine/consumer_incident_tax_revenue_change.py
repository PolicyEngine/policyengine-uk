from policyengine_uk.model_api import *


class consumer_incident_tax_revenue_change(Variable):
    label = "consumer-incident tax revenue change"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        consumption = household("consumption", period)
        if (
            household.simulation.dataset is not None
            and household("consumption", period).sum() != 0
        ):
            weight = household("household_weight", period)
            share = consumption / (consumption * weight).sum()
        else:
            share = consumption / 846e9
        revenue_change = parameters(
            period
        ).gov.contrib.policyengine.budget.consumer_incident_tax_change
        return revenue_change * share * 1e9
