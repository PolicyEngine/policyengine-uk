from policyengine_uk.model_api import *


class firm_special_rate_pool_carried_forward(Variable):
    value_type = float
    entity = Firm
    label = "Firm special rate pool carried forward"
    documentation = (
        "Tax written-down value of the special rate pool carried to next year: "
        "the pool balance less the writing-down allowance, plus the part of "
        "this year's first-year allowance spend not relieved by the allowance, "
        "which joins the pool next year."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/section/58"

    def formula(firm, period, parameters):
        available = firm("firm_special_rate_first_year_allowance_available", period)
        written_down = firm("firm_special_rate_pool_balance", period) - firm(
            "firm_special_rate_pool_writing_down_allowance", period
        )
        fya_spend = firm("firm_capex_special_rate_new", period) - firm(
            "firm_aia_special_rate_new", period
        )
        fya_balance = where(
            available,
            fya_spend - firm("firm_special_rate_first_year_allowance", period),
            0,
        )
        return written_down + fya_balance
