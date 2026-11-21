from policyengine_uk.model_api import *
from policyengine_uk.entities import Firm


class firm_vat_voluntarily_registered(Variable):
    label = "Voluntarily registered for VAT"
    documentation = "Whether the firm is registered for VAT although its taxable turnover does not exceed the registration threshold."
    entity = Firm
    definition_period = YEAR
    value_type = bool
    default_value = False
