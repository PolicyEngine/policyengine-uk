from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_is_rhl_property(Variable):
    value_type = bool
    entity = Firm
    label = "Firm's property is a qualifying retail, hospitality or leisure property"
    documentation = "Whether the firm's property qualifies as retail, hospitality or leisure (RHL) for business rates in England: the RHL multipliers from 2026-27, RHL relief to 2025-26 and the higher RHL small business rate relief thresholds from 2027-28."
    definition_period = YEAR
    default_value = False
