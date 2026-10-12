from policyengine_uk.model_api import *


class household_uc_unreported_company_holdings(Variable):
    value_type = float
    entity = Household
    label = "Household company holdings disregarded for Universal Credit, unreported benunits"
    documentation = (
        "The disregarded holdings (uc_company_holding_disregard) of people in "
        "benunits without reported UC capital. They are taken out of the "
        "household's capital before it is shared among those benunits' "
        "claimants and partners, so no benunit counts any part of a "
        "disregarded holding. A holding is shares, held within the "
        "household's corporate_wealth, so no more than that is taken out: a "
        "holding entered without matching corporate_wealth cannot remove "
        "savings or property."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        person = household.members
        has_reported_capital = person.benunit("uc_reported_capital", period) >= 0
        holdings = household.sum(
            person("uc_company_holding_disregard", period) * ~has_reported_capital
        )
        corporate_wealth = max_(0, household("corporate_wealth", period))
        return min_(holdings, corporate_wealth)
