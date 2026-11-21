from policyengine_uk.model_api import *


class firm_annual_investment_allowance_limit(Variable):
    value_type = float
    entity = Firm
    label = "Firm annual investment allowance limit"
    documentation = (
        "The annual investment allowance limit available to the firm: the "
        "statutory maximum times the firm's share of a limit shared with group "
        "companies or related businesses."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/section/51A"

    def formula(firm, period, parameters):
        limit = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.annual_investment_allowance.limit
        return limit * firm("firm_aia_share", period)
