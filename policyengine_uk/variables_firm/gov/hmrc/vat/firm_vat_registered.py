from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_vat_registered(Variable):
    value_type = bool
    entity = Firm
    label = "VAT registered"
    definition_period = YEAR
    documentation = (
        "Whether the firm is registered for VAT based on turnover threshold"
    )

    def formula(firm, period, parameters):
        # Use annual_turnover_k from our existing firm variables
        # Convert from thousands to pounds
        turnover = firm("annual_turnover_k", period) * 1000
        threshold = parameters(period).gov.hmrc.vat.registration_threshold

        return turnover > threshold
