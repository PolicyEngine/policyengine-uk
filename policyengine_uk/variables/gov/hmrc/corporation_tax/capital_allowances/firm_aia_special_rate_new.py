from policyengine_uk.model_api import *


class firm_aia_special_rate_new(Variable):
    value_type = float
    entity = Firm
    label = "Firm annual investment allowance on new special-rate plant"
    documentation = (
        "Annual investment allowance claimed on new special-rate plant and machinery. The allowance goes "
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
        p = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.first_year_allowances
        limit = firm("firm_annual_investment_allowance_limit", period)
        after_special_used = limit - firm("firm_aia_special_rate_used", period)
        after_main_used = after_special_used - firm("firm_aia_main_pool_used", period)
        # Where the main-rate first-year allowance is lower, new main-rate
        # spend not fully expensed takes the allowance first.
        main_first = p.main_rate < p.special_rate
        after_main_new = (
            after_main_used - firm("firm_aia_main_pool_new", period)
            if main_first
            else after_main_used
        )
        remaining = where(
            firm("firm_special_rate_first_year_allowance_available", period),
            after_main_new,
            after_special_used,
        )
        return min_(firm("firm_capex_special_rate_new", period), max_(remaining, 0))
