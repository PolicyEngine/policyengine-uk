from policyengine_uk.model_api import *


class is_child_for_universal_credit(Variable):
    value_type = bool
    entity = Person
    label = "Child for Universal Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2012/5/section/40"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_credit.elements.child.eligibility
        return person("age", period) < p.child_age_limit
