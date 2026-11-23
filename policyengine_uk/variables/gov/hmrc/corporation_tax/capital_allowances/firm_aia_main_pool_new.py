from policyengine_uk.model_api import *


class firm_aia_main_pool_new(Variable):
    value_type = float
    entity = Firm
    label = "Firm annual investment allowance on new main-rate plant"
    documentation = (
        "Annual investment allowance claimed on new main-rate plant and machinery not claimed under full expensing. The allowance goes "
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
        available = firm("firm_special_rate_first_year_allowance_available", period)
        special_used = firm("firm_aia_special_rate_used", period)
        special_new_spend = firm("firm_capex_special_rate_new", period)
        # New special-rate spend without the first-year allowance comes
        # before second-hand main-rate spend, as in firm_aia_main_pool_used.
        special_new_without_fya = where(
            available, 0, min_(special_new_spend, max_(limit - special_used, 0))
        )
        after_used = max_(
            limit
            - special_used
            - special_new_without_fya
            - firm("firm_aia_main_pool_used", period),
            0,
        )
        # New special-rate spend with the first-year allowance comes before
        # this spend unless the main-rate first-year allowance is lower.
        main_first = p.main_rate < p.special_rate
        special_new_with_fya = where(
            available & (not main_first), min_(special_new_spend, after_used), 0
        )
        remaining = max_(after_used - special_new_with_fya, 0)
        spend = firm("firm_main_pool_new_expenditure_after_full_expensing", period)
        return min_(spend, remaining)
