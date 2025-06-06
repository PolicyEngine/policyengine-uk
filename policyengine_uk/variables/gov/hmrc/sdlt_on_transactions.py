from policyengine_uk.model_api import *


class sdlt_on_transactions(Variable):
    label = "SDLT on property transactions"
    documentation = "Stamp Duty Land Tax on property transfers"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2003/14/section/55"

    adds = [
        "sdlt_on_residential_property_transactions",
        "sdlt_on_non_residential_property_transactions",
    ]
