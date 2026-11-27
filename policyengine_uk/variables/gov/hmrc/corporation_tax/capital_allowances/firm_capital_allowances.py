from policyengine_uk.model_api import *


class firm_capital_allowances(Variable):
    value_type = float
    entity = Firm
    label = "Firm capital allowances"
    documentation = (
        "Capital allowances claimed in the year, net of balancing charges: "
        "first-year allowances, the annual investment allowance, writing-down "
        "allowances and the structures and buildings allowance, less the main "
        "pool balancing charge and the balancing charge on disposals of fully "
        "expensed plant. Negative where the balancing charges exceed the "
        "allowances; deduct from trading profit."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/contents"
    adds = [
        "firm_full_expensing_allowance",
        "firm_special_rate_first_year_allowance",
        "firm_main_rate_first_year_allowance",
        "firm_annual_investment_allowance",
        "firm_main_pool_writing_down_allowance",
        "firm_special_rate_pool_writing_down_allowance",
        "firm_structures_and_buildings_allowance",
    ]
    subtracts = [
        "firm_main_pool_balancing_charge",
        "firm_full_expensing_balancing_charge",
    ]
