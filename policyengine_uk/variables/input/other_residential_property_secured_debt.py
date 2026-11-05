from policyengine_uk.model_api import *


class other_residential_property_secured_debt(Variable):
    value_type = float
    entity = Household
    label = "Debt secured on other residential property"
    documentation = (
        "Outstanding encumbrances secured specifically on the household's "
        "other residential property. Excludes main-home mortgage debt and unsecured "
        "debt. Deducted after sale expenses in UC regulation 49 valuation. "
        "The survey lacks reliable property-specific debt flags, so the "
        "default zero is a modelling approximation unless supplied explicitly."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = STOCK
    default_value = 0
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
    reference = "https://www.legislation.gov.uk/uksi/2013/376/regulation/49/1"
