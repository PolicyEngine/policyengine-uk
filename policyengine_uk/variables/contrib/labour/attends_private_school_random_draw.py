from policyengine_uk.model_api import *


class attends_private_school_random_draw(Variable):
    value_type = float
    entity = Person
    label = "Random draw for private school attendance"
    documentation = (
        "Random value [0,1) used to determine private school attendance. "
        "Generated in the dataset for reproducibility."
    )
    definition_period = YEAR
