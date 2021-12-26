from openfisca_uk.model_api import *


class corporate_wealth(Variable):
    label = "Corporate wealth"
    documentation = "Total owned wealth in corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class shareholding(Variable):
    label = "Share in the corporate sector"
    documentation = "Exposure to taxes on corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period, parameters):
        nbs = parameters(period).wealth.national_balance_sheet
        wealth = household("corporate_wealth", period)
        total_wealth = (wealth * household("household_weight", period)).sum()
        total_wealth = where(
            total_wealth > 0, total_wealth, nbs.household.financial_net_worth
        )
        return wealth / total_wealth


class corporate_tax_incidence(Variable):
    label = "Corporate tax incidence"
    documentation = (
        "Reduction in value of corporate wealth due to taxes on corporations"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(household, period):
        TAXES = [
            "corporate_sdlt_change_incidence",
            "business_rates_change_incidence",
        ]
        return add(household, period, TAXES)
