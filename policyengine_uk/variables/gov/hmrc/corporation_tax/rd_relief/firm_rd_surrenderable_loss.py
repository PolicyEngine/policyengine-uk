from policyengine_uk.model_api import *


class firm_rd_surrenderable_loss(Variable):
    value_type = float
    entity = Firm
    label = "Firm R&D surrenderable loss"
    documentation = (
        "Trading loss a company claiming SME R&D relief can surrender for a "
        "payable credit: the loss after capital allowances and the additional "
        "deduction, capped at the qualifying expenditure plus the additional "
        "deduction (section 1055 of the Corporation Tax Act 2009). Other "
        "reliefs for the loss are ignored."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2009/4/part/13/chapter/2"
    defined_for = "firm_claims_rd_sme_relief"

    def formula(firm, period, parameters):
        deduction = firm("firm_rd_additional_deduction", period)
        profit = (
            firm("firm_taxable_trading_profit", period)
            - firm("firm_capital_allowances", period)
            - deduction
        )
        cap = firm("firm_qualifying_rd_expenditure", period) + deduction
        return min_(max_(-profit, 0), cap)
