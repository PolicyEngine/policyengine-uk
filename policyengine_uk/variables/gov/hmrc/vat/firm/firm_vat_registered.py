from policyengine_uk.model_api import *


class firm_vat_registered(Variable):
    value_type = bool
    entity = Firm
    label = "Firm is VAT registered"
    definition_period = YEAR
    documentation = "Whether the firm is registered for VAT"

    def formula(firm, period, parameters):
        turnover = firm("firm_turnover", period)
        threshold = parameters(period).gov.hmrc.vat.registration_threshold
        return turnover > threshold
