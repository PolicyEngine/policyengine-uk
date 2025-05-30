from policyengine_uk.model_api import *


class corporate_incident_tax_revenue_change(Variable):
    label = "corporate-incident tax revenue change"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        share = household("shareholding", period)
        revenue_change = parameters(
            period
        ).gov.contrib.policyengine.budget.corporate_incident_tax_change
        return revenue_change * share * 1e9
