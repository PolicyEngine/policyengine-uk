from openfisca_uk.model_api import *


class main_residential_property_purchased(Variable):
    label = "Residential property bought (main)"
    documentation = "The price paid for the purchase of a residential property in the year, for use as a main residence. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class additional_residential_property_purchased(Variable):
    label = "Residential property bought (additional)"
    documentation = "The price paid for the purchase of a residential property in the year, for use as a second home or another non-main-residence purpose. Only include the value of a single purchase."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"


class main_residential_property_purchased_is_first_home(Variable):
    label = "Residential property bought is first home"
    documentation = "Whether the residential property bought this year as a main residence was as a first-time buyer."
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


class non_residential_rent(Variable):
    label = "Non-residential rent"
    documentation = "The total amount of rent paid by the household in the year for non-residential property."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
