from policyengine_uk.model_api import *


class wales_childcare_offer(Variable):
    value_type = float
    entity = BenUnit
    label = "Childcare Offer for Wales"
    documentation = (
        "The annual value of the childcare element of the Childcare Offer for "
        "Wales for the family's children. See wales_childcare_offer_per_child."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "wales_childcare_offer_eligible"
    adds = ["wales_childcare_offer_per_child"]
