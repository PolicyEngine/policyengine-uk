from policyengine_uk.model_api import *


class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = "savings interest income"
    documentation = "Income from interest on savings, gross of tax"
    definition_period = YEAR
    reference = "Income Tax (Trading and Other Income) Act 2005 s. 365(1)(a)"
    unit = GBP
    quantity_type = FLOW
    # Grown by households' interest received per person (ONS HAXV, D.41, then
    # OBR financial assets and deposit rates). Per person, because household
    # weights already grow by population (#1862).
    uprating = (
        "gov.economic_assumptions.indices.ons.per_capita.household_interest_income"
    )
