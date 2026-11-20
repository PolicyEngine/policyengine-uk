from policyengine_uk.model_api import *


class receives_higher_rate_attendance_allowance(Variable):
    label = "Receives attendance allowance at the higher rate"
    entity = Person
    definition_period = YEAR
    value_type = bool
    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/65"

    def formula(person, period, parameters):
        category = person("aa_category", period)
        return category == category.possible_values.HIGHER
