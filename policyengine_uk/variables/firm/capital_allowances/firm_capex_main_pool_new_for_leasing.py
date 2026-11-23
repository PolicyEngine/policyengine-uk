from policyengine_uk.model_api import *


class firm_capex_main_pool_new_for_leasing(Variable):
    value_type = float
    entity = Firm
    label = "Firm new main-rate plant and machinery expenditure for leasing"
    documentation = (
        "Expenditure in the year on unused, not second-hand main-rate plant "
        "and machinery provided for leasing. General exclusion 6 in section "
        "46(2) of the Capital Allowances Act 2001 bars full expensing on it, "
        "so it takes the annual investment allowance, then the main-rate "
        "first-year allowance, and the rest joins the main pool. Assumes the "
        "lessee conditions in section 46(4B) are met, so the main-rate "
        "first-year allowance is available. Background plant leased with a "
        "building, which keeps full expensing under section 46(4A), belongs "
        "in firm_capex_main_pool_new. Excludes cars."
    )
    definition_period = YEAR
    hidden_input = True
    default_value = 0
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ukpga/2001/2/section/46",
        "https://www.legislation.gov.uk/ukpga/2001/2/section/45U",
    )
