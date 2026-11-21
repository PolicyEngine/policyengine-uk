from policyengine_uk.model_api import *


class firm_aia_share(Variable):
    value_type = float
    entity = Firm
    label = "Firm share of the annual investment allowance"
    documentation = "Share of the annual investment allowance limit allocated to this firm. Group companies and related businesses share one limit; a stand-alone business has the whole limit."
    definition_period = YEAR
    unit = "/1"
    default_value = 1
