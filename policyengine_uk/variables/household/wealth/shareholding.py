from policyengine_uk.model_api import *


class shareholding(Variable):
    label = "Share in the corporate sector"
    documentation = "Exposure to taxes on corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        wealth = household("corporate_sector_wealth", period)
        if household.simulation.dataset is not None:
            weight = household("household_weight", period)
            weighted_total = (wealth * weight).sum()
            if weighted_total != 0:
                return wealth / weighted_total
        wealth = parameters(period).household.wealth
        nbs = wealth.national_balance_sheet
        wealth = household("corporate_sector_wealth", period)
        total_wealth = nbs.household.financial_net_worth
        return wealth / total_wealth
