from policyengine_uk.model_api import *


class WTC_basic_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit basic element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = GBP
    defined_for = "is_WTC_eligible"

    def formula(benunit, period, parameters):
        return parameters(
            period
        ).gov.dwp.tax_credits.working_tax_credit.elements.basic
