from openfisca_uk.model_api import *

class wtc_couple_element(Variable):
    label = "WTC couple element"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        wtc = parameters(period).hmrc.tax_credits.working_tax_credit
        return wtc.elements.couple * benunit("is_joint_benunit", period)
