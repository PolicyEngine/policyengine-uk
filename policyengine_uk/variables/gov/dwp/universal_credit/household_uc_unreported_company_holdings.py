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
        "disregarded holding."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK

    def formula(household, period, parameters):
        person = household.members
        has_reported_capital = person.benunit("uc_reported_capital", period) >= 0
        holdings = person("uc_company_holding_disregard", period)
        return household.sum(holdings * ~has_reported_capital)
