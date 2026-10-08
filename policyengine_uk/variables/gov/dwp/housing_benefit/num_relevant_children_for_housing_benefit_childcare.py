from policyengine_uk.model_api import *


class num_relevant_children_for_housing_benefit_childcare(Variable):
    value_type = int
    entity = BenUnit
    definition_period = YEAR
    label = "Children with qualifying paid Housing Benefit childcare"
    documentation = "Counts only children with positive qualifying per-child charges. An older sibling or child with no paid qualifying care cannot increase the one-child cap. Provider and exact September age conditions are applied to each child's charges."
    reference = "https://www.legislation.gov.uk/uksi/2006/213/regulation/27"

    def formula(benunit, period, parameters):
        return benunit.sum(
            benunit.members("housing_benefit_qualifying_childcare_costs", period) > 0
        )
