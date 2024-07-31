from policyengine_uk.model_api import *


class land_only_wealth(Variable):
    label = "land-only wealth"
    documentation = "Total value of all land-only plots."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK


class primary_residence_value(Variable):
    label = "primary residence value"
    documentation = "Total value of the primary residence."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK


class other_residential_property_value(Variable):
    label = "other residence value"
    documentation = "Total value of all non-primary residential property."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
