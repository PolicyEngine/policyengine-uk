from policyengine_uk.model_api import *


class CouncilTaxBand(Enum):
    A = "Band A"
    B = "Band B"
    C = "Band C"
    D = "Band D"
    E = "Band E"
    F = "Band F"
    G = "Band G"
    H = "Band H"
    I = "Band I"  # Used in Wales


class council_tax_band(Variable):
    value_type = Enum
    possible_values = CouncilTaxBand
    default_value = CouncilTaxBand.D
    entity = Household
    label = "Council Tax band"
    definition_period = YEAR
