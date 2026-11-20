from policyengine_uk.model_api import *


class rent_paid_as_lodger(Variable):
    value_type = float
    entity = Person
    label = "rent paid to the householder as a lodger"
    documentation = (
        "Rent this person pays the householder for lodging without meals in "
        "the householder's home, where this person lives as a member of the "
        "household outside the householder's benefit unit. The Family "
        "Resources Survey records it on the payer (CVPAY where CONVBL is not "
        "1). Annual amount; the weekly means-test rules divide it by 52."
    )
    definition_period = YEAR
    unit = GBP
    uprating = "gov.economic_assumptions.indices.obr.per_capita.gdp"
