from policyengine_uk.model_api import *


class childcare_grant_child_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Child is eligible for Childcare Grant"
    documentation = (
        "Whether the child satisfies the Childcare Grant child-age condition."
    )
    definition_period = YEAR
    defined_for = "is_child"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.childcare_grant.eligible_child.max_age
        has_sen = person("childcare_grant_child_has_special_educational_needs", period)
        max_age = where(has_sen, p.special_educational_needs, p.standard)
        return person("age", period) < max_age
