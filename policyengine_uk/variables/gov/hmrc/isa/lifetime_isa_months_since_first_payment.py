from policyengine_uk.model_api import *


class lifetime_isa_months_since_first_payment(Variable):
    value_type = int
    entity = Person
    label = "Months since the first Lifetime ISA payment"
    documentation = "Completed months between the first Lifetime ISA payment and the first-home withdrawal, including continuity through qualifying Lifetime ISA transfers. The value describes the recorded annual first-home withdrawal; separate transaction dates are not modelled."
    definition_period = YEAR
    unit = "month"
    quantity_type = STOCK
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule/paragraph/6"
