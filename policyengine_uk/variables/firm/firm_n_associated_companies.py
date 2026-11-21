from policyengine_uk.model_api import *


class firm_n_associated_companies(Variable):
    value_type = int
    entity = Firm
    label = "Number of associated companies"
    documentation = "Number of companies associated with the firm for corporation tax purposes (excluding the firm itself), which divides the small profits and upper limits."
    definition_period = YEAR
