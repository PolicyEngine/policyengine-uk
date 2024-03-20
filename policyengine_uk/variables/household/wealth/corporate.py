from policyengine_uk.model_api import *


class shareholding(Variable):
    label = "Share in the corporate sector"
    documentation = "Exposure to taxes on corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        wealth = parameters(period).household.wealth
        nbs = wealth.national_balance_sheet
        wealth = household("corporate_wealth", period)
        total_wealth = nbs.household.financial_net_worth
        return wealth / total_wealth


class corporate_tax_incidence(Variable):
    label = "Corporate tax incidence"
    documentation = (
        "Reduction in value of corporate wealth due to taxes on corporations"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = [
        "corporate_sdlt_change_incidence",
        "business_rates_change_incidence",
    ]
