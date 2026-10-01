from policyengine_uk.model_api import *


class rent_paid_as_lodger(Variable):
    value_type = float
    entity = Person
    label = "Rent paid as a lodger"
    documentation = (
        "Rent this person pays the householder for lodging only in the "
        "householder's home."
    )
    definition_period = YEAR
    unit = GBP
