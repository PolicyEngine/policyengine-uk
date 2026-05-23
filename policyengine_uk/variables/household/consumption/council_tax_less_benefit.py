from policyengine_uk.model_api import *


class council_tax_less_benefit(Variable):
    label = "Council Tax (less CTB)"
    documentation = "Council Tax minus Council Tax Reduction"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        return max_(
            0,
            household("council_tax", period)
            - household("council_tax_reduction", period),
        )
