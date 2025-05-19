from policyengine_uk.model_api import *


class admitted_patient_visits(Variable):
    label = "admitted patient visits"
    documentation = "Number of admitted patient visits by this person."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
