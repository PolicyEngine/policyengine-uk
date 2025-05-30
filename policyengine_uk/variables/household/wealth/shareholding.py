from policyengine_uk.model_api import *


class shareholding(Variable):
    label = "Share in the corporate sector"
    documentation = "Exposure to taxes on corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        wealth = household("corporate_wealth", period)
        if (
            household.simulation.dataset is not None
            and household("corporate_wealth", period).sum() != 0
        ):
            weight = household("household_weight", period)
            return wealth / (wealth * weight).sum()
        wealth = parameters(period).household.wealth
        nbs = wealth.national_balance_sheet
        wealth = household("corporate_wealth", period)
        total_wealth = nbs.household.financial_net_worth
        return wealth / total_wealth
