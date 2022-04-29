from openfisca_uk.model_api import *


@uprated(by="wealth.national_balance_sheet.household.financial_net_worth")
class corporate_wealth(Variable):
    label = "Corporate wealth"
    documentation = "Total owned wealth in corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK


class shareholding(Variable):
    label = "Share in the corporate sector"
    documentation = "Exposure to taxes on corporations"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        wealth = parameters(period).wealth
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

    def formula(household, period):
        TAXES = [
            "corporate_sdlt_change_incidence",
            "business_rates_change_incidence",
        ]
        return add(household, period, TAXES)
