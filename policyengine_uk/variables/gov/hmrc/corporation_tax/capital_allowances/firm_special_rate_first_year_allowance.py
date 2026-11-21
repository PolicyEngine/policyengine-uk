from policyengine_uk.model_api import *


class firm_special_rate_first_year_allowance(Variable):
    value_type = float
    entity = Firm
    label = "Firm special-rate first-year allowance"
    documentation = (
        "First-year allowance a company claims on new special-rate plant and "
        "machinery that the annual investment allowance does not cover: 50% "
        "under section 45S of the Capital Allowances Act 2001, and the SR "
        "allowance from April 2021 to March 2023. Companies only."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/45S",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/52",
    )

    def formula(firm, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.first_year_allowances.special_rate
        available = firm("firm_special_rate_first_year_allowance_available", period)
        remaining = firm("firm_capex_special_rate_new", period) - firm(
            "firm_aia_special_rate_new", period
        )
        return where(available, rate * remaining, 0)
