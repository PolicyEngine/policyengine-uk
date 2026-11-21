from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_flat_rate_sector_percentage(Variable):
    label = "VAT flat rate sector percentage"
    documentation = (
        "Flat rate percentage for the firm's business category, as a share "
        "(0.12 for 12%). Defaults to the rate for any other activity not "
        "listed elsewhere; supply a value to use another category."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = "https://www.gov.uk/vat-flat-rate-scheme/how-much-you-pay"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.vat.flat_rate
        return np.full(firm.count, p.default_sector_rate)
