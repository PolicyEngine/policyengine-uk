from policyengine_uk.model_api import *


class council_tax_band(Variable):
    value_type = Enum
    possible_values = CouncilTaxBand
    default_value = CouncilTaxBand.D
    entity = Household
    label = "Council Tax band"
    definition_period = YEAR
