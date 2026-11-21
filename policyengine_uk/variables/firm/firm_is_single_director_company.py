from policyengine_uk.model_api import *


class firm_is_single_director_company(Variable):
    value_type = bool
    entity = Firm
    label = "Firm is a single-director company"
    documentation = "Whether the firm is a company whose only employee paid above the secondary threshold is a director, which excludes it from the Employment Allowance."
    definition_period = YEAR
    default_value = False
