from policyengine_uk.model_api import *


class rent_paid_as_boarder(Variable):
    value_type = float
    entity = Person
    label = "Rent paid as a boarder"
    documentation = (
        "Rent this person pays the householder for board and lodging "
        "(accommodation with at least some meals) in the householder's home."
    )
    definition_period = YEAR
    unit = GBP
