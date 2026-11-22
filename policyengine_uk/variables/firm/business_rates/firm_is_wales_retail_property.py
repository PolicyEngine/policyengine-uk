from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_is_wales_retail_property(Variable):
    value_type = bool
    entity = Firm
    label = (
        "Firm's Welsh property is described as a shop, kiosk, pharmacy or post office"
    )
    documentation = (
        "Whether the firm's property in Wales is described on the local "
        "rating list as a kiosk, pharmacy, post office, shop, or shop and "
        "post office, with premises. From 2026-27 such properties with "
        "rateable value below £51,000 pay the Welsh retail multiplier (WSI "
        "2025/1163 reg 3). Local-list properties only. From 2027-28 WSI "
        "2026/133 widens this lower multiplier to about 37 descriptions, "
        "including pubs, restaurants, hotels and leisure; that change is not "
        "modelled. Ignored outside Wales."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = False
    reference = "https://www.legislation.gov.uk/wsi/2025/1163/made"
