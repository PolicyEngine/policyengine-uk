from policyengine_uk.model_api import *


class firm_full_expensing_allowance(Variable):
    value_type = float
    entity = Firm
    label = "Firm full expensing allowance"
    documentation = (
        "First-year allowance a company claims on new main-rate plant and "
        "machinery: full expensing at 100% from April 2023, and the 130% "
        "super-deduction from April 2021 to March 2023. Companies only."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/45S",
        "https://www.legislation.gov.uk/ukpga/2021/26/section/9",
    )

    def formula(firm, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.first_year_allowances.full_expensing_rate
        is_company = (
            firm("firm_legal_form", period)
            == firm("firm_legal_form", period).possible_values.COMPANY
        )
        spend = firm("firm_capex_main_pool_new", period)
        return where(is_company, rate * spend, 0)
