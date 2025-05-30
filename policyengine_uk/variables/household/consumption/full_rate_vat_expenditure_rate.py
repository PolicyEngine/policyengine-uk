from policyengine_uk.model_api import *


class full_rate_vat_expenditure_rate(Variable):
    label = "VAT full-rated expenditure rate"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"
    default_value = 0.5
