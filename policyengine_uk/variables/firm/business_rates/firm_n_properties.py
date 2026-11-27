from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_n_properties(Variable):
    value_type = int
    entity = Firm
    label = "Number of non-domestic properties the firm occupies"
    documentation = (
        "How many non-domestic properties the firm occupies. The model treats "
        "the firm's rateable value as one aggregate property; this count only "
        "decides small business relief eligibility: SBRR in England and "
        "Wales, and the Small Business Bonus Scheme in Scotland."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = 1
