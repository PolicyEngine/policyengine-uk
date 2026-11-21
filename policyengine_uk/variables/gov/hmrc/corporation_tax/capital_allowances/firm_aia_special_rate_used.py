from policyengine_uk.model_api import *


class firm_aia_special_rate_used(Variable):
    value_type = float
    entity = Firm
    label = "Firm annual investment allowance on second-hand special-rate plant"
    documentation = (
        "Annual investment allowance claimed on second-hand special-rate plant and machinery. The allowance goes "
        "first to second-hand special-rate spend, then to new special-rate "
        "spend where no special-rate first-year allowance is available, then "
        "to second-hand main-rate spend, then to new special-rate spend where "
        "that first-year allowance is available, then to new main-rate spend "
        "not fully expensed. This order gives the most relief in the year."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/section/51A"

    def formula(firm, period, parameters):
        limit = firm("firm_annual_investment_allowance_limit", period)
        return min_(firm("firm_capex_special_rate_used", period), limit)
