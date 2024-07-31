from policyengine_uk.model_api import *


class business_wealth(Variable):
    label = "business wealth"
    documentation = "Business assets owned by this person where this person is self-employed, a director or partner."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    quantity_type = STOCK
