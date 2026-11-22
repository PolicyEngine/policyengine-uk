from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_is_live_music_venue(Variable):
    value_type = bool
    entity = Firm
    label = "Firm's property is a live music venue"
    documentation = (
        "Whether the firm's property is a live music venue, as opposed to a "
        "pub, for the pubs and live music venues business rates relief in "
        "England. Only matters together with firm_is_pub_or_live_music_venue: "
        "live music venues with rateable value of £1m or more keep 15% relief "
        "in 2027-28 and 2028-29, while pubs of any size get 35%."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = False
