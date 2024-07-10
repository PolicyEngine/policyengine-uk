from policyengine_uk.model_api import *


class SSP(Variable):
    value_type = float
    entity = Person
    label = "Statutory Sick Pay"
    definition_period = YEAR
    unit = GBP
    reference = "Social Security Contributions and Benefits Act 1992, Part XI"
