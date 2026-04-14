from policyengine_uk.model_api import *


class childcare_grant_eligible_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of eligible children for Childcare Grant"
    documentation = (
        "Number of children in the student's benefit unit who satisfy the Childcare Grant child-age rule."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("childcare_grant_child_eligible", period))
