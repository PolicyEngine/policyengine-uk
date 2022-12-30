from policyengine_uk.model_api import *

label = "Maintenance"


class housing_service_charges(Variable):
    value_type = float
    entity = Household
    label = "housing service charges"
    documentation = "Total amount spent on housing service charges"
    definition_period = YEAR
    unit = GBP


class water_and_sewerage_charges(Variable):
    value_type = float
    entity = Household
    label = "water and sewerage charges"
    documentation = "Total amount spent on water and sewerage charges"
    definition_period = YEAR


class employer_pension_contributions(Variable):
    value_type = float
    entity = Person
    label = "Employer pension contributions"
    documentation = "Total amount spent on employer pension contributions"
    definition_period = YEAR
    unit = GBP


class maintenance_expenses(Variable):
    value_type = float
    entity = Person
    label = "maintenance expenses"
    definition_period = YEAR
    unit = GBP


class mortgage_interest_repayment(Variable):
    value_type = float
    entity = Household
    label = "mortgage interest repayments"
    documentation = "Total amount spent on mortgage interest repayments"
    definition_period = YEAR
    unit = GBP


class mortgage_capital_repayment(Variable):
    value_type = float
    entity = Household
    label = "mortgage capital repayments"
    definition_period = YEAR
    unit = GBP


class council_tax(Variable):
    value_type = float
    entity = Household
    label = "Council Tax"
    documentation: str = "Gross amount spent on Council Tax, before discounts"
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    uprating: str = "calibration.uprating.council_tax"
