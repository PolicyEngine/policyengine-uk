from policyengine_uk.model_api import *


class council_tax(Variable):
    value_type = float
    entity = Household
    label = "Council Tax"
    documentation = (
        "Gross annual Council Tax liability before Council Tax Reduction. "
        "This is currently supplied by the household dataset rather than "
        "recomputed from local authority council tax schedules."
    )
    definition_period = YEAR
    unit = GBP
    quantity_type = FLOW
