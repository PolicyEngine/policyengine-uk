from policyengine_uk.model_api import *
from policyengine_uk.utils.dates import birth_day


class birth_year(Variable):
    value_type = int
    entity = Person
    label = "The birth year of the person"
    documentation = (
        "The calendar year of the person's date of birth (date_of_birth where given)."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        return birth_day(person, period) // 10000
