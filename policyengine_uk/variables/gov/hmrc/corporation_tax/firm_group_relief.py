from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_group_relief(Variable):
    value_type = float
    entity = Firm
    label = "Firm group relief"
    documentation = (
        "Group relief deducted from the firm's total profits under CTA 2010 "
        "Part 5: firm_group_relief_claimed, floored at zero and capped at "
        "the firm's total profits (s.138(b) and s.140(7)). It is deducted "
        "after all other deductions except carried-forward losses and Part "
        "5A relief (s.137(4)-(5)), so it also reduces the profits against "
        "which carried-forward losses are restricted (s.269ZFA). Consortium "
        "limits, overlapping periods and the surrenderer's matching "
        "surrender are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/137",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/138",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/140",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269ZFA",
    )

    def formula(firm, period, parameters):
        claimed = max_(firm("firm_group_relief_claimed", period), 0)
        profits = max_(firm("firm_profits_before_losses", period), 0)
        return min_(claimed, profits)
