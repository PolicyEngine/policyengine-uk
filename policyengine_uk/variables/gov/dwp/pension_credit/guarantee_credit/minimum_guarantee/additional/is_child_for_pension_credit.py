from policyengine_uk.model_api import *


class is_child_for_pension_credit(Variable):
    value_type = bool
    entity = Person
    label = "Child for Pension Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2002/1792/schedule/IIA"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pension_credit.guarantee_credit.child.eligibility
        return person("age", period) < p.child_age_limit
