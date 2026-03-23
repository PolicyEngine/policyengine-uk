from policyengine_uk.model_api import *


class council_tax_reduction_income_below_applicable_amount(Variable):
    value_type = bool
    entity = BenUnit
    label = "CTR applicable income is at or below the applicable amount"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        applicable_amount = benunit("council_tax_reduction_applicable_amount", period)
        applicable_income = benunit("council_tax_reduction_applicable_income", period)
        return applicable_income <= applicable_amount
