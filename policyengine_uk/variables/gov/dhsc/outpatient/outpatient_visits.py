from policyengine_uk.model_api import *


class outpatient_visits(Variable):
    label = "outpatient visits"
    documentation = "Number of outpatient visits by this person."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
