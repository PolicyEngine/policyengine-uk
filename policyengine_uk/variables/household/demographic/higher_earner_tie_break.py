from policyengine_uk.model_api import *


class higher_earner_tie_break(Variable):
    value_type = float
    entity = Person
    label = "Random draw for tie-breaking in higher earner determination"
    documentation = (
        "Random value [0,1) used to break ties when determining the higher earner. "
        "Generated in the dataset for reproducibility."
    )
    definition_period = YEAR
