from policyengine_uk.model_api import *

label = "Transactions"


class property_purchased(Variable):
    label = "All property bought this year"
    documentation = "Whether all property wealth was bought this year"
    entity = Household
    definition_period = YEAR
    value_type = bool
    default_value = True


class cumulative_residential_rent(Variable):
    label = "Cumulative residential rent"
    documentation = "Total rent paid over the lifetime of the residential property a tenancy is held for."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP


class cumulative_non_residential_rent(Variable):
    label = "Cumulative non-residential rent"
    documentation = "Total rent paid over the lifetime of the non-residential property a tenancy is held for."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP


class non_residential_rent(Variable):
    label = "Non-residential rent"
    documentation = "The total amount of rent paid by the household in the year for non-residential property."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
