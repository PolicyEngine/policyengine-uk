from policyengine_uk.model_api import *


class a_and_e_visits(Variable):
    label = "A&E visits"
    documentation = "Number of A&E visits by this person."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
