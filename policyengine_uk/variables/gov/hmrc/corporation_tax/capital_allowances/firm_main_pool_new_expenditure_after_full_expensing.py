from policyengine_uk.model_api import *


class firm_main_pool_new_expenditure_after_full_expensing(Variable):
    value_type = float
    entity = Firm
    label = "Firm new main-rate expenditure not claimed under full expensing"
    documentation = (
        "New main-rate plant and machinery expenditure left for the annual "
        "investment allowance or the main-rate first-year allowance: plant "
        "for leasing, which general exclusion 6 bars from full expensing, "
        "plus other new main-rate spend for an unincorporated business, or "
        "for a company when full expensing is not available."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/45S",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/46",
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
        for_leasing = firm("firm_capex_main_pool_new_for_leasing", period)
        return where(is_company & (rate > 0), 0, spend) + for_leasing
