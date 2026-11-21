from policyengine_uk.model_api import *


class firm_main_pool_carried_forward(Variable):
    value_type = float
    entity = Firm
    label = "Firm main pool carried forward"
    documentation = (
        "Tax written-down value of the main pool carried to next year: the "
        "pool balance less the writing-down allowance (zero after a balancing "
        "charge), plus the part of this year's first-year allowance spend not "
        "relieved by the allowance, which joins the pool next year."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/section/58"

    def formula(firm, period, parameters):
        p = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.first_year_allowances
        balance = max_(firm("firm_main_pool_balance", period), 0)
        written_down = balance - firm("firm_main_pool_writing_down_allowance", period)
        fully_expensed = firm("firm_capex_main_pool_new", period) - firm(
            "firm_main_pool_new_expenditure_after_full_expensing", period
        )
        full_expensing_balance = max_(
            fully_expensed - firm("firm_full_expensing_allowance", period), 0
        )
        fya_spend = firm(
            "firm_main_pool_new_expenditure_after_full_expensing", period
        ) - firm("firm_aia_main_pool_new", period)
        fya_balance = (
            fya_spend - firm("firm_main_rate_first_year_allowance", period)
            if p.main_rate > 0
            else 0
        )
        return written_down + full_expensing_balance + fya_balance
