from policyengine_uk.model_api import *


class bus_pass_eligible(Variable):
    label = "bus pass eligible"
    documentation = "Whether the person travels free under the concessionary rule supplied by the dataset; this input is not a pass-eligibility calculator."
    entity = Person
    definition_period = YEAR
    value_type = bool
