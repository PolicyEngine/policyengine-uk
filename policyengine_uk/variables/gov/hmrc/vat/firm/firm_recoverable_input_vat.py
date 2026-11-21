from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_recoverable_input_vat(Variable):
    label = "Recoverable input VAT"
    documentation = (
        "Input VAT the firm can deduct from output VAT after the partial "
        "exemption restriction."
    )
    entity = Firm
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/1994/23/section/26"

    def formula(firm, period, parameters):
        input_vat = firm("firm_input_vat", period)
        share = firm("firm_partial_exemption_recovery_share", period)
        return input_vat * share
