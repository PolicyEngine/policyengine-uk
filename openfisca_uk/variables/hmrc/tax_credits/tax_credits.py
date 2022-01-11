from openfisca_uk.model_api import *

class tax_credits_below_minimum(Variable):
    label = "Tax Credits are below the minimum"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        min_benefit = parameters(period).hmrc.tax_credits.minimum_benefit
        total = (
            benunit("ctc_pre_minimum", period)
            + benunit("wtc_pre_minimum", period)
        )
        return total < min_benefit

class tax_credits(Variable):
    label = "Tax Credits"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return add(benunit, period, ["working_tax_credit", "child_tax_credit"])
