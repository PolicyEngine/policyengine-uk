from policyengine_uk.model_api import *


class council_tax_less_benefit(Variable):
    label = "Council Tax after Council Tax Reduction"
    documentation = (
        "Gross Council Tax liability minus Council Tax Reduction, floored "
        "at zero. During the CTR transition, the reduction may be modelled "
        "for supported local schemes or reported for unsupported schemes."
    )
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
