from policyengine_uk.model_api import *


class high_income_incident_tax_change(Variable):
    label = "high income-incident tax revenue change"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        if household.simulation.dataset is None:
            return 0

        total_income = household.members("total_income", period)
        high_income = household.sum(max_(total_income - 100e3, 0))
        weight = household("household_weight", period)
        share = high_income / (high_income * weight).sum()
        revenue_change = parameters(
            period
        ).gov.contrib.policyengine.budget.high_income_incident_tax_change
        return revenue_change * 1e9 * share
