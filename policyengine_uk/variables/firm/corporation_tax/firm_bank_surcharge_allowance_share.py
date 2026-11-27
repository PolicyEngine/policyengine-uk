from policyengine_uk.entities import Firm
from policyengine_uk.model_api import *


class firm_bank_surcharge_allowance_share(Variable):
    value_type = float
    entity = Firm
    label = "Firm share of the bank surcharge allowance"
    documentation = (
        "Share of the bank surcharge allowance available to this banking "
        "company. A group with more than one banking company shares one "
        "allowance, allocated between them by the group's allocation "
        "statement; the shares sum to at most one across the group. The "
        "default of 1 gives a stand-alone bank the whole allowance."
    )
    definition_period = YEAR
    hidden_input = True
    unit = "/1"
    default_value = 1
    reference = (
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269DE",
        "https://www.legislation.gov.uk/ukpga/2010/4/section/269DF",
    )
