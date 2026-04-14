from policyengine_uk.model_api import *


class bursary_fund_16_to_19_participation_costs(Variable):
    value_type = float
    entity = Person
    label = "Participation costs for 16 to 19 Bursary Fund support"
    documentation = (
        "Annual participation costs that the 16 to 19 Bursary Fund can cover, such as travel, books, "
        "equipment, or specialist clothing required for study."
    )
    definition_period = YEAR
    unit = GBP
    default_value = 0
    set_input = set_input_dispatch_by_period
