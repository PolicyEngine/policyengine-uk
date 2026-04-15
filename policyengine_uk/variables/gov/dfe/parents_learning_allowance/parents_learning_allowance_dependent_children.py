from policyengine_uk.model_api import *


class parents_learning_allowance_dependent_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Dependent children for Parents' Learning Allowance"
    documentation = (
        "Number of children in the student's benefit unit counted as dependent children for the first-pass "
        "Parents' Learning Allowance model."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_child", period))
