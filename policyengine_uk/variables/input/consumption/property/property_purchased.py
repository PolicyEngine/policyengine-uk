from policyengine_uk.model_api import *


class property_purchased(Variable):
    label = "All property bought this year"
    documentation = "Whether all property wealth was bought this year"
    entity = Household
    definition_period = YEAR
    value_type = bool
    # Fail-safe default: a household has NOT bought all its property this year.
    # main_residential_property_purchased is computed as
    # main_residence_value * property_purchased, so a True default charges
    # every household stamp duty on its full property wealth (~£370bn of
    # phantom SDLT). Population datasets set this explicitly for the small
    # share of genuine purchasers; the household calculator and tests set
    # main_residential_property_purchased directly. False is the correct
    # neutral default for any household where it is not set.
    default_value = False
