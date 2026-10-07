from policyengine_uk.model_api import *


class is_child_receiving_extended_childcare(Variable):
    value_type = bool
    entity = Person
    label = "child is receiving extended childcare entitlement"
    documentation = (
        "Whether this child gets working parent hours beyond any universal or "
        "targeted hours. A 3- or 4-year-old whose family uses no more than the "
        "universal 15 hours a week is on the universal entitlement only."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("extended_childcare_entitlement_per_child", period) > 0
