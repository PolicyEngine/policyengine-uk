from policyengine_uk.model_api import *


class firm_main_rate_first_year_allowance(Variable):
    value_type = float
    entity = Firm
    label = "Firm main-rate first-year allowance"
    documentation = (
        "First-year allowance under section 45U of the Capital Allowances Act "
        "2001 on new main-rate plant and machinery that neither full expensing "
        "nor the annual investment allowance covers. Companies and "
        "unincorporated businesses can claim it."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/45U",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/52",
    )

    def formula(firm, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.first_year_allowances.main_rate
        spend = firm("firm_main_pool_new_expenditure_after_full_expensing", period)
        remaining = spend - firm("firm_aia_main_pool_new", period)
        return rate * remaining
