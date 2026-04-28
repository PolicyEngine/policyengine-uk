from policyengine_uk.model_api import *


class meets_qualifying_young_person_age_condition_for_pension_credit(Variable):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person age condition for Pension Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/regulation/4A"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit.child.eligibility
        age = person("age", period)
        return (age >= p.child_age_limit) & (age < p.qualifying_young_person_age_limit)
