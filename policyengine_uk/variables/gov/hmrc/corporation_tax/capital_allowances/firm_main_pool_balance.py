from policyengine_uk.model_api import *


class firm_main_pool_balance(Variable):
    value_type = float
    entity = Firm
    label = "Firm main pool balance before writing-down allowance"
    documentation = (
        "Available qualifying expenditure in the main pool less disposal "
        "receipts (AQE less TDR): the balance brought forward plus main-rate "
        "spend that no first-year allowance covers, less disposal proceeds. "
        "Disposal receipts are reduced by the full expensing balancing charge "
        "(section 59A), so a disposal of fully expensed plant does not reduce "
        "the pool. "
        "Spend on which a first-year allowance is claimed joins the pool only "
        "next year (section 58(5) of the Capital Allowances Act 2001). "
        "Negative where disposals exceed the pool."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/55",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/58",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/59A",
    )

    def formula(firm, period, parameters):
        p = parameters(
            period
        ).gov.hmrc.corporation_tax.capital_allowances.first_year_allowances
        used_unrelieved = firm("firm_capex_main_pool_used", period) - firm(
            "firm_aia_main_pool_used", period
        )
        new_unrelieved = firm(
            "firm_main_pool_new_expenditure_after_full_expensing", period
        ) - firm("firm_aia_main_pool_new", period)
        new_pooled = new_unrelieved if p.main_rate == 0 else 0
        disposals = max_(
            firm("firm_disposal_proceeds_main_pool", period)
            - firm("firm_full_expensing_balancing_charge", period),
            0,
        )
        return (
            firm("firm_main_pool_brought_forward", period)
            + used_unrelieved
            + new_pooled
            - disposals
        )
