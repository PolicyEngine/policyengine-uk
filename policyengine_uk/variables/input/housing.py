from policyengine_uk.model_api import *

label = "Housing"


class rent(Variable):
    label = "Rent"
    documentation = (
        "The total amount of rent paid by the household in the year."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = FLOW


class CouncilTaxBand(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"


class council_tax_band(Variable):
    value_type = Enum
    possible_values = CouncilTaxBand
    default_value = CouncilTaxBand.D
    entity = Household
    label = "Council Tax band"
    definition_period = YEAR
