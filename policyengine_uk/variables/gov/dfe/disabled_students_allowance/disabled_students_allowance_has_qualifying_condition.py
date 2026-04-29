from policyengine_uk.model_api import *


class disabled_students_allowance_has_qualifying_condition(Variable):
    value_type = bool
    entity = Person
    label = "Has a qualifying condition for Disabled Students' Allowance"
    documentation = (
        "Whether the person has a disability, long-term health condition, mental "
        "health condition, or specific learning difficulty that can qualify for "
        "Disabled Students' Allowance. This can be set explicitly in simulations. "
        "By default, the model uses observed disability-benefit receipt or explicit "
        "blindness input, which is narrower than the full legal concept."
    )
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return person("is_disabled_for_benefits", period) | person("is_blind", period)
