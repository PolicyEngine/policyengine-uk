from policyengine_uk.model_api import *


class lifetime_isa_payments(Variable):
    value_type = float
    entity = Person
    label = "Lifetime ISA qualifying payments"
    documentation = "Current-year qualifying additions to a Lifetime ISA, including qualifying transfers from other ISA types. Exclude bonuses, interest and growth, Lifetime-ISA-to-Lifetime-ISA transfers, returned failed-purchase withdrawals, defaulted payments and rebated fees. Contributions at ages 40 to 49 assume an account first funded before age 40. Annual age and payment timing are approximations."
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/regulation/10A"
