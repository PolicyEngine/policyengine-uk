from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_n_properties(Variable):
    value_type = int
    entity = Firm
    label = "Number of non-domestic properties the firm occupies"
    documentation = (
        "How many non-domestic properties the firm occupies in England. The "
        "model treats the firm's rateable value as one aggregate property; "
        "this count only decides small business rate relief eligibility."
    )
    definition_period = YEAR
    default_value = 1
