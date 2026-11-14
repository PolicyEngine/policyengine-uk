from policyengine_uk.model_api import *


class qualifies_for_apprentice_minimum_wage(Variable):
    value_type = bool
    entity = Person
    label = "Qualifies for the apprentice minimum wage"
    definition_period = YEAR
    reference = "https://www.legislation.gov.uk/uksi/2015/621/regulation/5"

    def formula(person, period, parameters):
        p = parameters(period).gov.hmrc.minimum_wage
        return person("is_apprentice", period) & (
            (person("age", period) < p.apprentice_age_limit)
            | person("is_in_first_year_of_apprenticeship", period)
        )
