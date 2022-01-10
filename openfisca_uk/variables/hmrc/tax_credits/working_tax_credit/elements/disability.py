from openfisca_uk.model_api import *

class wtc_disability_element(Variable):
    label = "WTC disability element"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        wtc = parameters(period).hmrc.tax_credits.working_tax_credit
        return wtc.elements.disability * benunit("is_work_disadvantaged", period)
