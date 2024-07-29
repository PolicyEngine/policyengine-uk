from policyengine_uk.model_api import *


class uc_childcare_element_eligible_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Universal Credit childcare element eligible children"
    documentation = "Number of eligible children eligible for the childcare element of the Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        eligible_child = (
            benunit.members("uc_individual_child_element", period) > 0
        )
        return benunit.sum(eligible_child)
