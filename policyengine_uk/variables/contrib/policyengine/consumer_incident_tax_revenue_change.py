from policyengine_uk.model_api import *


class consumer_incident_tax_revenue_change(Variable):
    label = "consumer-incident tax revenue change"
    documentation = (
        "A lump-sum revenue change that a reform sets "
        "(gov.contrib.policyengine.budget.consumer_incident_tax_change, in "
        "£ billion), shared across households by consumption_shareholding. A "
        "household situation takes no share unless consumption_shareholding "
        "is set."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        share = household("consumption_shareholding", period)
        revenue_change = parameters(
            period
        ).gov.contrib.policyengine.budget.consumer_incident_tax_change
        return revenue_change * share * 1e9
