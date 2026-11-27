from policyengine_uk.model_api import *


class firm_id(Variable):
    value_type = int
    entity = Firm
    label = "Firm ID"
    documentation = "Identifier of the firm. Unique within a dataset or situation."
    definition_period = YEAR
    hidden_input = True
