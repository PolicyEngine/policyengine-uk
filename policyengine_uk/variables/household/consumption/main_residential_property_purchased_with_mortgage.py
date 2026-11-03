from policyengine_uk.model_api import *


class main_residential_property_purchased_with_mortgage(Variable):
    value_type = bool
    entity = Household
    label = "Main-home purchase uses qualifying Lifetime ISA financing"
    documentation = "Whether this main-home purchase uses a secured legal mortgage or regulated home purchase plan qualifying for the Lifetime ISA exemption. Apply the statutory financing restrictions, including the connected-person lender exclusion from 6 April 2024 and restrictions on buy-to-let financing; an existing mortgage balance alone does not establish this fact."
    definition_period = YEAR
    quantity_type = STOCK
    default_value = False
    reference = "https://www.gov.uk/guidance/lifetime-isa-withdrawals-for-a-first-time-residential-purchase"
