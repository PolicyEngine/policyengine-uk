from policyengine_uk.model_api import *


class has_lifetime_isa(Variable):
    label = "holds a Lifetime ISA"
    documentation = (
        "Whether the person holds a Lifetime ISA with a positive balance. A "
        "dataset that stores this column keeps the stored value: it is "
        "recomputed only when not stored, so a reform or situation that edits "
        "lifetime_isa_balance leaves it unchanged."
    )
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period):
        return person("lifetime_isa_balance", period) > 0
