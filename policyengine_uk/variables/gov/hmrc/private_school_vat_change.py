from policyengine_uk.model_api import *


class private_school_vat_change(Variable):
    label = "change in private school VAT"
    documentation = (
        "Change in private school VAT from its baseline. Household taxes "
        "include VAT only as a change, so this is the head they include; "
        "government tax revenue includes the level."
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"
    adds = ["private_school_vat"]
    subtracts = ["baseline_private_school_vat"]
