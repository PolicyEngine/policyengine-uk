from policyengine_uk.model_api import *


class childcare_grant_child_has_special_educational_needs(Variable):
    value_type = bool
    entity = Person
    label = "Child has special educational needs for Childcare Grant"
    documentation = (
        "Whether the child should be treated as having special educational needs for Childcare Grant age rules. "
        "This must currently be set explicitly in simulations because the core model "
        "does not expose a reliable special-educational-needs proxy."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period
    default_value = False
