from policyengine_uk.model_api import *


class other_tax_credits(Variable):
    label = "other miscellaneous tax credits for Income Tax"
    documentation = """Includes Venture Capital Trusts, Enterprise Investment Schemes, 
Seed Enterprise Investment Schemes, Community Investment Tax Relief, maintenance/alimony payments, 
Social Investment Tax Relief and foreign tax relief on income. Landlords' tax reduction for
residential finance costs is property_finance_cost_relief, not this."""
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
