from policyengine_uk.model_api import *


class meets_qualifying_young_person_age_condition_for_child_tax_credit(Variable):
    value_type = bool
    entity = Person
    label = "Meets qualifying young person age condition for Child Tax Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/2007/regulation/5"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.child_tax_credit.eligibility
        age = person("age", period)
        return (age >= p.child_age_limit) & (age < p.qualifying_young_person_age_limit)
