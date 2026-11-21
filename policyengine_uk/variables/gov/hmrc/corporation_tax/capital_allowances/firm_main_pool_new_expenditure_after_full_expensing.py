from policyengine_uk.model_api import *


class firm_main_pool_new_expenditure_after_full_expensing(Variable):
    value_type = float
    entity = Firm
    label = "Firm new main-rate expenditure not claimed under full expensing"
    documentation = (
        "New main-rate plant and machinery expenditure left for the annual "
        "investment allowance or the main-rate first-year allowance: all of it "
        "for an unincorporated business, or for a company when full expensing "
        "is not available."
    )
    definition_period = YEAR
    unit = GBP

    def formula(firm, period, parameters):
        rate = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.first_year_allowances.full_expensing_rate
        is_company = (
            firm("firm_legal_form", period)
            == firm("firm_legal_form", period).possible_values.COMPANY
        )
        spend = firm("firm_capex_main_pool_new", period)
        return where(is_company & (rate > 0), 0, spend)
