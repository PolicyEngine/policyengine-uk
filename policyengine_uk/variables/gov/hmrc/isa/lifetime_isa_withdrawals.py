from policyengine_uk.model_api import *


class lifetime_isa_withdrawals(Variable):
    value_type = float
    entity = Person
    label = "Gross Lifetime ISA withdrawals"
    documentation = "Gross annual removals from a Lifetime ISA, including any amount withheld for the withdrawal charge. Exclude qualifying transfers to another Lifetime ISA and withdrawals on death. This flow does not update the supplied Lifetime ISA balance. Annual age and transaction conditions are assumed to apply to the recorded withdrawals."
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
    default_value = 0
    reference = "https://www.legislation.gov.uk/uksi/1998/1870/schedule"
