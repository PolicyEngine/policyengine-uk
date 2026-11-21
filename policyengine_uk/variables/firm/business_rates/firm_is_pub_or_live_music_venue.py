from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_is_pub_or_live_music_venue(Variable):
    value_type = bool
    entity = Firm
    label = "Firm's property is a pub or live music venue"
    documentation = "Whether the firm's property is a pub or live music venue eligible for the pubs and live music venues business rates relief in England."
    definition_period = YEAR
    default_value = False
