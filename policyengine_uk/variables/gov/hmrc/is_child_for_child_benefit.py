from policyengine_uk.model_api import *


class is_child_for_child_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Child for Child Benefit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/142"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.child_benefit.eligibility
        return person("age", period) < p.child_age_limit
