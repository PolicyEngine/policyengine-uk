from policyengine_uk.model_api import *


class savings_interest_income(Variable):
    value_type = float
    entity = Person
    label = "Savings interest outside tax-free accounts"
    documentation = (
        "Interest gross of tax, excluding ISA and other exempt interest. "
        "Tax-free interest is additional. Supported dataset loaders convert "
        "legacy gross savings inputs to this convention before calculation."
    )
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
