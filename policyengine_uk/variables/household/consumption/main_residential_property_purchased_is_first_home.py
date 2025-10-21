from policyengine_uk.model_api import *


class main_residential_property_purchased_is_first_home(Variable):
    label = "Residential property bought is first home"
    documentation = (
        "Whether the residential property bought this year as a main residence "
        "was as a first-time buyer. Generated stochastically in the dataset."
    )
    entity = Household
    definition_period = YEAR
    value_type = bool

    # No formula - when in dataset, OpenFisca uses dataset value automatically
    # For policy calculator (non-dataset), defaults to False
    default_value = False
