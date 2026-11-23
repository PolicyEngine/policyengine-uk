from policyengine_uk.model_api import *


class firm_aia_main_pool_used(Variable):
    value_type = float
    entity = Firm
    label = "Firm annual investment allowance on second-hand main-rate plant"
    documentation = (
        "Annual investment allowance claimed on second-hand main-rate plant and machinery. The allowance goes "
        "first to second-hand special-rate spend, then to new special-rate "
        "spend where no special-rate first-year allowance is available, then "
        "to second-hand main-rate spend. It then goes to new special-rate "
        "spend that has the special-rate first-year allowance and to new "
        "main-rate spend not fully expensed (in practice plant for leasing), "
        "taking first whichever has the lower first-year allowance rate; on "
        "a tie the special-rate spend goes first. This order gives the most "
        "relief in the year."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/section/51A"

    def formula(firm, period, parameters):
        limit = firm("firm_annual_investment_allowance_limit", period)
        after_special_used = max_(limit - firm("firm_aia_special_rate_used", period), 0)
        special_new_first = where(
            firm("firm_special_rate_first_year_allowance_available", period),
            0,
            min_(firm("firm_capex_special_rate_new", period), after_special_used),
        )
        remaining = max_(after_special_used - special_new_first, 0)
        return min_(firm("firm_capex_main_pool_used", period), remaining)
