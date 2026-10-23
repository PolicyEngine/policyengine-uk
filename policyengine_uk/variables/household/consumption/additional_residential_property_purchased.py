from policyengine_uk.model_api import *


class additional_residential_property_purchased(Variable):
    label = "Residential property bought (additional)"
    documentation = (
        "The price paid for a single residential property bought in the year "
        "that is not a replacement of the household's main residence, such as "
        "a second home or a property to let, so that the higher rates for "
        "additional dwellings apply (Finance Act 2003 Schedule 4ZA). Only "
        "include the value of a single purchase. A main-residence purchase "
        "(property_purchased) does not imply one: the household's stock of "
        "other residential property (other_residential_property_value) is not "
        "a purchase, so this is nil unless set directly or by a dataset that "
        "imputes additional-dwelling purchases."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = dict(
        title="Finance Act 2003 Schedule 4ZA",
        href="https://www.legislation.gov.uk/ukpga/2003/14/schedule/4ZA",
    )
