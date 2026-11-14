from policyengine_uk.model_api import *


class lifetime_isa_terminally_ill(Variable):
    value_type = bool
    entity = Person
    label = "Terminal illness certified for a Lifetime ISA withdrawal"
    documentation = "Whether written evidence from a registered medical practitioner states that the investor is expected to live for less than one year, for the Lifetime ISA withdrawal exemption. This input does not derive eligibility for other health benefits."
    definition_period = YEAR
    quantity_type = STOCK
    default_value = False
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/4"
