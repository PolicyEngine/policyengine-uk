from policyengine_uk.model_api import *


class uc_individual_disabled_child_element(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit disabled child element"
    definition_period = YEAR
    unit = GBP
    defined_for = "is_disabled_for_benefits"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.child.disabled
        child = person("is_child", period)
        return (child * p.amount) * MONTHS_IN_YEAR
