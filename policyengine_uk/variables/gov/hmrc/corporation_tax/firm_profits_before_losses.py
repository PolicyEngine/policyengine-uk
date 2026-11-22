from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_profits_before_losses(Variable):
    value_type = float
    entity = Firm
    label = "Firm profits before losses brought forward"
    documentation = (
        "Taxable trading profit less capital allowances and the R&D "
        "additional deduction, plus the taxable R&D expenditure credit and "
        "non-trading profits. Negative when the firm makes a loss in the year."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "firm_liable_to_corporation_tax"
    reference = "https://www.legislation.gov.uk/ukpga/2010/4/section/4"

    def formula(firm, period, parameters):
        additions = add(
            firm,
            period,
            [
                "firm_taxable_trading_profit",
                "firm_rd_expenditure_credit",
                "firm_non_trading_profits",
            ],
        )
        deductions = add(
            firm,
            period,
            ["firm_capital_allowances", "firm_rd_additional_deduction"],
        )
        return additions - deductions
