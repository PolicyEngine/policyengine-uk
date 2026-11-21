from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_vat(Variable):
    label = "Firm VAT"
    documentation = (
        "Net VAT the firm pays to HMRC in the year; negative for a repayment. "
        "Zero for a firm that is not registered."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1994/23/section/25"

    def formula(firm, period, parameters):
        registered = firm("firm_vat_registered", period)
        liability = firm("firm_vat_liability_if_registered", period)
        return where(registered, liability, 0)
