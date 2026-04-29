from policyengine_uk.model_api import *


class tax_credits(Variable):
    value_type = float
    entity = BenUnit
    label = "Tax Credits"
    documentation = "Value of the Tax Credits (benefits) for this family"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        if not parameters(period).gov.dwp.tax_credits.active:
            return benunit.empty_array()
        amount = add(
            benunit,
            period,
            ["working_tax_credit_pre_minimum", "child_tax_credit_pre_minimum"],
        )
        min_benefit = parameters(period).gov.dwp.tax_credits.min_benefit
        return where(amount < min_benefit, 0, amount)
