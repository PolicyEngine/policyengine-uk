from policyengine_uk.model_api import *


class firm_annual_investment_allowance(Variable):
    value_type = float
    entity = Firm
    label = "Firm annual investment allowance"
    documentation = "Annual investment allowance claimed on plant and machinery expenditure in the year."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/section/51A"
    adds = [
        "firm_aia_special_rate_used",
        "firm_aia_main_pool_used",
        "firm_aia_special_rate_new",
        "firm_aia_main_pool_new",
    ]
