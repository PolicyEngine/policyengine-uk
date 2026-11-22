from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_taxable_profit(Variable):
    value_type = float
    entity = Firm
    label = "Firm taxable total profits"
    documentation = (
        "Profits chargeable to corporation tax after carried-forward losses. "
        "Group relief is not modelled."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/4"

    def formula(firm, period, parameters):
        profits = firm("firm_profits_before_losses", period)
        losses_used = firm("firm_losses_used", period)
        return max_(profits - losses_used, 0)
