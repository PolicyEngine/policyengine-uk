from policyengine_uk.model_api import *


class education_grants(Variable):
    label = "Education grants"
    documentation = "Grants for education"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
