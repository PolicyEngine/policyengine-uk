from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_vat_normal_liability(Variable):
    label = "VAT liability under normal accounting"
    documentation = (
        "Output VAT less recoverable input VAT. A negative value is a "
        "repayment from HMRC."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1994/23/section/25"
    adds = ["firm_output_vat"]
    subtracts = ["firm_recoverable_input_vat"]
