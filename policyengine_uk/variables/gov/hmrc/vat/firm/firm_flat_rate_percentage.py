from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_flat_rate_percentage(Variable):
    label = "VAT flat rate percentage"
    documentation = (
        "Flat rate percentage the firm applies: the limited cost trader rate "
        "if it is a limited cost trader, otherwise its sector percentage. The "
        "1-point discount in the first year of registration is not modelled."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = "/1"
    reference = "https://www.legislation.gov.uk/uksi/2017/295/made"

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.vat.flat_rate
        limited_cost = firm("firm_is_limited_cost_trader", period)
        sector = firm("firm_flat_rate_sector_percentage", period)
        return where(limited_cost, p.limited_cost_trader_rate, sector)
