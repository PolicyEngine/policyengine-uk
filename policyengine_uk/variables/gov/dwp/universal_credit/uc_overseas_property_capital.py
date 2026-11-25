from policyengine_uk.model_api import *
from policyengine_uk.utils.capital_valuation import less_sale_expenses


class uc_overseas_property_capital(Variable):
    value_type = float
    entity = Household
    label = "Universal Credit net overseas property capital"
    documentation = (
        "Assessment-year value of overseas land and property less regulation "
        "49 sale expenses. Assumes no Schedule 10 disregard; the broad input "
        "does not identify asset-level disregards or secured debt. Valued "
        "separately from financial reports and allocated through uc_property_capital."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/49"

    def formula(household, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.means_test.capital
        return less_sale_expenses(
            max_(0, household("overseas_property_value", period)),
            p.sale_expenses.rate,
            p.round_down,
        )
