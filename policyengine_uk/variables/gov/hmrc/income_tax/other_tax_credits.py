from policyengine_uk.model_api import *


class other_tax_credits(Variable):
    label = "other miscellaneous tax credits for Income Tax"
    documentation = """Includes Venture Capital Trusts, Enterprise Investment Schemes, 
Seed Enterprise Investment Schemes, Community Investment Tax Relief, maintenance/alimony payments, 
Social Investment Tax Relief and foreign tax relief on income. Landlords' tax reduction for
residential finance costs is property_finance_cost_relief, not this. These are tax reductions
deducted at Step 6 of the Income Tax calculation, so with the other reductions they are limited
to the tax calculated at Step 5 and never offset the Step 7 charges (income_tax_reductions).
Because they are held together, the further limit on the EIS, SEIS, social investment, VCT and
community investment reductions in ITA 2007 s. 29(4A) to (4C), the Step 5 tax less the tax
treated as deducted from Gift Aid donations, is not applied."""
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = dict(
        title="Income Tax Act 2007 s. 29",
        href="https://www.legislation.gov.uk/ukpga/2007/3/section/29",
    )
