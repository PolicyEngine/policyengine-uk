from policyengine_uk.model_api import *


class stamp_duty_land_tax(Variable):
    label = "Stamp Duty Land Tax"
    documentation = "Total tax liability for Stamp Duty Land Tax"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/part/4"
    defined_for = "sdlt_liable"
    adds = [
        "sdlt_on_transactions",
        "sdlt_on_rent",
    ]
