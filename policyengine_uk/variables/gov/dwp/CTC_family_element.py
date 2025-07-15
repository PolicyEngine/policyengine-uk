from policyengine_uk.model_api import *


class CTC_family_element(Variable):
    value_type = float
    entity = BenUnit
    label = "CTC entitlement in the Family Element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = GBP
    defined_for = "is_CTC_eligible"

    def formula(benunit, period, parameters):
        return parameters(
            period
        ).gov.dwp.tax_credits.child_tax_credit.elements.family_element
