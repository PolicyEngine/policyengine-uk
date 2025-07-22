from policyengine_uk.model_api import *


class WTC_severely_disabled_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit severely disabled element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = GBP

    def formula(benunit, period, parameters):
        WTC = parameters(period).gov.dwp.tax_credits.working_tax_credit
        amount = (
            benunit("num_severely_disabled_adults", period)
            * WTC.elements.severely_disabled
        )
        return benunit("is_WTC_eligible", period) * amount
