from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_is_wales_higher_multiplier_excluded(Variable):
    value_type = bool
    entity = Firm
    label = (
        "Firm's Welsh property has a description excluded from the higher multiplier"
    )
    documentation = (
        "Whether the firm's property in Wales is described on the local "
        "rating list as one of the 19 descriptions that WSI 2025/1163 reg 4 "
        "keeps on the standard multiplier above £100,000: ambulance station, "
        "auxiliary defence establishment, cemetery, college, crematorium, "
        "fire station, health centre, hospital, law court, leisure centre, "
        "library, museum, police station, prison, school, sports centre, "
        "surgery, swimming pool or university (each with premises). Ignored "
        "outside Wales."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = False
    reference = "https://www.legislation.gov.uk/wsi/2025/1163/made"
