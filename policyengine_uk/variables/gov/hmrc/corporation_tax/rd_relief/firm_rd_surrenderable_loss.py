from policyengine_uk.model_api import *


class firm_rd_surrenderable_loss(Variable):
    value_type = float
    entity = Firm
    label = "Firm R&D surrenderable loss"
    documentation = (
        "Trading loss a company claiming SME R&D relief can surrender for a "
        "payable credit (section 1055 of the Corporation Tax Act 2009): the "
        "unrelieved trading loss after capital allowances and the additional "
        "deduction, capped at the qualifying expenditure plus the additional "
        "deduction. The loss is unrelieved after the relief that was or could "
        "have been obtained against total profits of the same accounting "
        "period under section 37(3)(a) of the Corporation Tax Act 2010 "
        "(section 1056(2)(a)), so the loss is reduced by the company's "
        "positive non-trading profits, against which firm_profits_before_losses "
        "already sets it. Losses brought forward are ignored, as section "
        "1056(3) requires. Carry-back, group and consortium relief (section "
        "1056(2)(b) and (c)) are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1055",
        "https://www.legislation.gov.uk/ukpga/2009/4/section/1056",
    )
    defined_for = "firm_claims_rd_sme_relief"

    def formula(firm, period, parameters):
        deduction = firm("firm_rd_additional_deduction", period)
        trading_profit = (
            firm("firm_taxable_trading_profit", period)
            - firm("firm_capital_allowances", period)
            - deduction
        )
        trading_loss = max_(-trading_profit, 0)
        # s.1056(2)(a): relief against total profits of the same period,
        # whether or not claimed, reduces the loss.
        same_period_relief = max_(firm("firm_non_trading_profits", period), 0)
        unrelieved = max_(trading_loss - same_period_relief, 0)
        cap = firm("firm_qualifying_rd_expenditure", period) + deduction
        return min_(unrelieved, cap)
