from policyengine_uk.model_api import *


class lifetime_isa_withdrawals_towards_first_home(Variable):
    value_type = float
    entity = Person
    label = "Lifetime ISA withdrawals paid for a first home"
    documentation = "Part of gross Lifetime ISA withdrawals paid directly to an eligible conveyancer towards the purchase price of a first home, with the required declarations and completion or return procedures satisfied. Exclude fees and amounts paid through the investor. Include a purchase above the property price cap, which pays a reduced charge from 29 October 2026. Ownership, UK location, financing, holding period and price conditions are checked separately."
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/6"
