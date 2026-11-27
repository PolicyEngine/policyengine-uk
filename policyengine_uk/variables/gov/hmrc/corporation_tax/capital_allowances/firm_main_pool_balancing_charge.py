from policyengine_uk.model_api import *


class firm_main_pool_balancing_charge(Variable):
    value_type = float
    entity = Firm
    label = "Firm main pool balancing charge"
    documentation = (
        "Balancing charge where disposal receipts in the main pool exceed its "
        "available qualifying expenditure (section 55(2) of the Capital "
        "Allowances Act 2001)."
    )
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2001/2/section/55"

    def formula(firm, period, parameters):
        return max_(-firm("firm_main_pool_balance", period), 0)
