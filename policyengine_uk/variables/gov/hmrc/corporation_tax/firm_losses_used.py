from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_losses_used(Variable):
    value_type = float
    entity = Firm
    label = "Firm losses brought forward used"
    documentation = (
        "Carried-forward losses set against the year's profits, up to the "
        "deductions allowance plus 50% of profits above it. Losses are treated "
        "as one pool against total profits; the separate trading and "
        "non-trading caps are not distinguished. Profits are taken after "
        "Part 5 group relief (firm_group_relief), which comes first."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269ZD",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269ZFA",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269ZR",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax.losses
        # Part 5 group relief is deducted first (CTA 2010 s.137(4)-(5)).
        profits = max_(
            firm("firm_profits_before_losses", period)
            - firm("firm_group_relief", period),
            0,
        )
        allowance = p.deductions_allowance * firm(
            "firm_deductions_allowance_share", period
        )
        relevant_maximum = allowance + p.restriction_rate * max_(profits - allowance, 0)
        losses = firm("firm_losses_brought_forward", period)
        return min_(losses, min_(relevant_maximum, profits))
