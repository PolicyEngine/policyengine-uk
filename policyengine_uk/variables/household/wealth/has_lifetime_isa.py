from policyengine_uk.model_api import *


class has_lifetime_isa(Variable):
    label = "holds a Lifetime ISA"
    documentation = "Whether the person holds a Lifetime ISA with a positive balance."
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period):
        return person("lifetime_isa_balance", period) > 0
