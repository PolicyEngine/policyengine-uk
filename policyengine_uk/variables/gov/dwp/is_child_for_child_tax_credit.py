from policyengine_uk.model_api import *


class is_child_for_child_tax_credit(Variable):
    value_type = bool
    entity = Person
    label = "Child for Child Tax Credit"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/ukpga/2002/21/section/8"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.tax_credits.child_tax_credit.eligibility
        return person("age", period) < p.child_age_limit
