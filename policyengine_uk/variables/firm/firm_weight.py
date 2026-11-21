from policyengine_uk.model_api import *


class firm_weight(Variable):
    value_type = float
    entity = Firm
    label = "Firm weight"
    documentation = "Number of firms in the population this firm represents. Defaults to one, so a firm in a situation counts once."
    definition_period = YEAR
    default_value = 1
