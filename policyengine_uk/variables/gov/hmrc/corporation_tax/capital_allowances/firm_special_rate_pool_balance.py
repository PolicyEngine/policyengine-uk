from policyengine_uk.model_api import *


class firm_special_rate_pool_balance(Variable):
    value_type = float
    entity = Firm
    label = "Firm special rate pool balance before writing-down allowance"
    documentation = (
        "Available qualifying expenditure in the special rate pool: the "
        "balance brought forward plus special-rate spend that neither the "
        "annual investment allowance nor a first-year allowance covers. Spend "
        "on which a first-year allowance is claimed joins the pool only next "
        "year. Disposals from the special rate pool are not modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/104D",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/58",
    )

    def formula(firm, period, parameters):
        available = firm("firm_special_rate_first_year_allowance_available", period)
        used_unrelieved = firm("firm_capex_special_rate_used", period) - firm(
            "firm_aia_special_rate_used", period
        )
        new_unrelieved = firm("firm_capex_special_rate_new", period) - firm(
            "firm_aia_special_rate_new", period
        )
        new_pooled = where(available, 0, new_unrelieved)
        return (
            firm("firm_special_rate_pool_brought_forward", period)
            + used_unrelieved
            + new_pooled
        )
