from policyengine_uk.model_api import *


class firm_capex_structures(Variable):
    value_type = float
    entity = Firm
    label = "Firm structures and buildings expenditure"
    documentation = "Qualifying expenditure in the year on non-residential structures and buildings brought into qualifying use this year, for the structures and buildings allowance."
    definition_period = YEAR
    unit = GBP
