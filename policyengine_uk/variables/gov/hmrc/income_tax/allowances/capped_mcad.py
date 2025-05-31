from policyengine_uk.model_api import *


class capped_mcad(Variable):
    label = "capped Married Couples' Allowance deduction"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        capping_value = add(
            person, period, ["income_tax_pre_charges", "CB_HITC"]
        )
        return min_(
            person("married_couples_allowance_deduction", period),
            capping_value,
        )
