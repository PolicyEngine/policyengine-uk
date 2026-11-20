from policyengine_uk.model_api import *


class childcare_grant_child_eligible(Variable):
    value_type = bool
    entity = Person
    label = "Child is eligible for Childcare Grant"
    documentation = (
        "Whether a dependent child of the student satisfies the Childcare "
        "Grant age condition: under 15, or under 17 with special educational "
        "needs, immediately before the academic year begins."
    )
    definition_period = YEAR
    defined_for = "is_dependent_child_for_student_support"
    reference = "https://www.legislation.gov.uk/uksi/2011/1986/regulation/45"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.childcare_grant.eligible_child.max_age
        has_sen = person("childcare_grant_child_has_special_educational_needs", period)
        max_age = where(has_sen, p.special_educational_needs, p.standard)
        return person("age", period) < max_age
