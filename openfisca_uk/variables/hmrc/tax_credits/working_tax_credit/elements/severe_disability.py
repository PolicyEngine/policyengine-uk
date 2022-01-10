from openfisca_uk.model_api import *

class wtc_severe_disability_element(Variable):
    label = "WTC severe disability element"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        wtc = parameters(period).hmrc.tax_credits.working_tax_credit
        is_severely_disabled = benunit.any(benunit.members("is_severely_disabled", period))
        return wtc.elements.disability * is_severely_disabled
