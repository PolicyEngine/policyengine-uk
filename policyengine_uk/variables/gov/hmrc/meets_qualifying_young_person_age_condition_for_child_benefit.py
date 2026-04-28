from policyengine_uk.model_api import *


class meets_qualifying_young_person_age_condition_for_child_benefit(Variable):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person age condition for Child Benefit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/142"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.child_benefit.eligibility
        age = person("age", period)
        return (age >= p.child_age_limit) & (age < p.qualifying_young_person_age_limit)
