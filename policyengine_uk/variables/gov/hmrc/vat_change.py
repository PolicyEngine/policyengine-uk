from policyengine_uk.model_api import *


class vat_change(Variable):
    label = "change in VAT liability"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    adds = ["vat"]
    subtracts = ["baseline_vat"]
