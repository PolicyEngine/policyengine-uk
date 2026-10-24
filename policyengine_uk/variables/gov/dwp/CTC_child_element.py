from policyengine_uk.model_api import *


class CTC_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Child Tax Credit child element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = GBP

    def formula(benunit, period, parameters):
        person = benunit.members
        child_tax_credit = parameters(period).gov.dwp.tax_credits.child_tax_credit
        children = benunit.sum(person("is_CTC_child_element_included", period))
        return child_tax_credit.elements.child_element * children
