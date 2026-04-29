from policyengine_uk.model_api import *


class bursary_fund_16_to_19(Variable):
    value_type = float
    entity = Person
    label = "16 to 19 Bursary Fund"
    documentation = (
        "First-pass vulnerable-group 16 to 19 Bursary Fund support. "
        "The model pays actual participation costs up to the vulnerable-group maximum."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "bursary_fund_16_to_19_vulnerable_group_eligible"

    def formula(person, period, parameters):
        p = parameters(period).gov.dfe.bursary_fund_16_to_19.vulnerable_groups
        participation_costs = person(
            "bursary_fund_16_to_19_participation_costs", period
        )
        return min_(participation_costs, p.max_amount)
