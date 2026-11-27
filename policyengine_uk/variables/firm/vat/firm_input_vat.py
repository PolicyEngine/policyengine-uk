from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_input_vat(Variable):
    label = "Input VAT"
    documentation = "VAT the firm is charged on its purchases in the year that would be recoverable before any partial exemption restriction."
    entity = Firm
    definition_period = YEAR
    hidden_input = True
    value_type = float
    unit = GBP
