from policyengine_uk.model_api import *


class child_benefit_less_tax_charge(Variable):
    label = "Child Benefit (less tax charge)"
    documentation = (
        "Child Benefit, minus the Child Benefit High-Income Tax Charge"
    )
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = ["child_benefit"]
    subtracts = ["CB_HITC"]
