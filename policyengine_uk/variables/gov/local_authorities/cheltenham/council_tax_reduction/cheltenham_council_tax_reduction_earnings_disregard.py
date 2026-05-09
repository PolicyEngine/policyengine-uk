from policyengine_uk.model_api import *


class cheltenham_council_tax_reduction_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Cheltenham Council Tax Support weekly earnings disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://democracy.cheltenham.gov.uk/documents/s53359/Appendix%209%20-%20Council%20270226%20Council%20Tax%20Support%20Scheme%20for%20Working%20Age%20Customers%202026-27%20Final.pdf"

    def formula(benunit, period, parameters):
        ctr = parameters(period).gov.local_authorities.cheltenham.council_tax_reduction
        return ctr.earnings_disregard.maximum
