from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_taxable_profit(Variable):
    value_type = float
    entity = Firm
    label = "Firm taxable total profits"
    documentation = (
        "Profits chargeable to corporation tax: total profits less Part 5 "
        "group relief, then carried-forward losses, then Part 5A group "
        "relief for carried-forward losses (CTA 2010 s.137(4)-(5))."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/4"

    def formula(firm, period, parameters):
        profits = firm("firm_profits_before_losses", period)
        deductions = add(
            firm,
            period,
            [
                "firm_group_relief",
                "firm_losses_used",
                "firm_group_relief_for_carried_forward_losses",
            ],
        )
        return max_(profits - deductions, 0)
