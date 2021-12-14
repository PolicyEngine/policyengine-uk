from openfisca_uk.model_api import *


class residential_property_purchased(Variable):
    label = "Residential property bought"
    documentation = "The price paid for the purchase of a residential property in the year. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class residential_property_purchased_is_first_home(Variable):
    label = "Residential property bought is first home"
    documentation = "Whether the residential property bought this year was as a first-time buyer."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class cumulative_residential_rent(Variable):
    label = "Cumulative residential rent"
    documentation = "Total rent paid over the lifetime of the residential property a tenancy is held for."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class non_residential_property_purchased(Variable):
    label = "Non-residential property bought"
    documentation = "The price paid for the purchase of a non-residential property in the year. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class cumulative_non_residential_rent(Variable):
    label = "Cumulative non-residential rent"
    documentation = "Total rent paid over the lifetime of the non-residential property a tenancy is held for."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class rent(Variable):
    label = "Rent"
    documentation = (
        "The total amount of rent paid by the household in the year."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
