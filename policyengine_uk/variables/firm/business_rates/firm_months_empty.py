from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_months_empty(Variable):
    value_type = int
    entity = Firm
    label = "Months the firm's property was already empty at the start of the year"
    documentation = (
        "For an unoccupied property, how many months it had already been "
        "continuously empty before the start of the year. The empty property "
        "exemption covers only what is left of the exemption period. Ignored "
        "when the property is occupied."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = 0
