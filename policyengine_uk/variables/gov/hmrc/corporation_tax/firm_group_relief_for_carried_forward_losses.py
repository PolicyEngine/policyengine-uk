from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_group_relief_for_carried_forward_losses(Variable):
    value_type = float
    entity = Firm
    label = "Firm group relief for carried-forward losses"
    documentation = (
        "Group relief for carried-forward losses under CTA 2010 Part 5A, from "
        "1 April 2017: firm_group_relief_for_carried_forward_losses_claimed, "
        "floored at zero and limited to the firm's relevant maximum (the "
        "deductions allowance plus 50% of profits above it) less its own "
        "carried-forward losses used (ss.188DB, 188DD and 269ZD(3)(j)). It is "
        "not given while the firm's own carried-forward losses are not all "
        "used (s.188CD)."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/188CD",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/188DB",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/188DD",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269ZD",
    )

    def formula(firm, period, parameters):
        p = parameters(period).gov.hmrc.corporation_tax.losses
        if not p.group_relief_for_carried_forward_losses_applies:
            return np.zeros(firm.count)
        profits = max_(
            firm("firm_profits_before_losses", period)
            - firm("firm_group_relief", period),
            0,
        )
        allowance = p.deductions_allowance * firm(
            "firm_deductions_allowance_share", period
        )
        relevant_maximum = allowance + p.restriction_rate * max_(profits - allowance, 0)
        losses_used = firm("firm_losses_used", period)
        own_fully_used = firm("firm_losses_brought_forward", period) <= losses_used
        room = max_(min_(relevant_maximum, profits) - losses_used, 0)
        claimed = max_(
            firm("firm_group_relief_for_carried_forward_losses_claimed", period), 0
        )
        return where(own_fully_used, min_(claimed, room), 0)
