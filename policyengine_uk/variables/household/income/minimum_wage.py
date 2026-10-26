from policyengine_uk.model_api import *


class minimum_wage(Variable):
    value_type = float
    entity = Person
    label = "Minimum wage"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.legislation.gov.uk/uksi/2015/621/regulation/5"

    def formula(person, period, parameters):
        MW = parameters(period).gov.hmrc.minimum_wage
        age = person("age", period)
        return where(
            person("qualifies_for_apprentice_minimum_wage", period),
            MW.apprentice,
            MW.non_apprentice.calc(age),
        )
