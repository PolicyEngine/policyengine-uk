from policyengine_uk.model_api import *


class property_purchased(Variable):
    label = "Main residence bought this year"
    documentation = (
        "Whether the household bought its main residence this year. It sets "
        "the main-residence purchase price (main_residential_property_purchased) "
        "only. Purchases of additional dwellings and of non-residential "
        "property are separate inputs, so a main-residence purchase never "
        "charges the higher rates for additional dwellings on the household's "
        "other property."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool
    # Fail-safe default: a household has NOT bought its home this year.
    # main_residential_property_purchased is computed as
    # main_residence_value * property_purchased, so a True default charges
    # every household stamp duty on its full main residence value. Population
    # datasets set this explicitly for the small share of genuine purchasers;
    # the household calculator and tests set main_residential_property_purchased
    # directly. False is the correct neutral default for any household where it
    # is not set.
    default_value = False
