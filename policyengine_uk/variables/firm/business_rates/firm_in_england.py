from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_in_england(Variable):
    value_type = bool
    entity = Firm
    label = "Firm's property is in England"
    documentation = "Whether the firm's property is in England. Business rates are modelled for England only; Scotland, Wales and Northern Ireland set their own rates and reliefs, so firm business rates are 0 elsewhere."
    definition_period = YEAR
    default_value = True
