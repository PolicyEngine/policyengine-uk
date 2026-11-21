from policyengine_uk.model_api import *


class FirmLegalForm(Enum):
    COMPANY = "Company"
    SOLE_TRADER = "Sole trader"
    PARTNERSHIP = "Partnership"
    OTHER = "Other"


class firm_legal_form(Variable):
    value_type = Enum
    entity = Firm
    label = "Firm legal form"
    documentation = "Legal form of the business: a company, a sole trader, a partnership or another form."
    definition_period = YEAR
    possible_values = FirmLegalForm
    default_value = FirmLegalForm.COMPANY
