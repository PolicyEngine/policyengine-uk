from policyengine_uk.model_api import *


class universal_childcare_entitlement_hours(Variable):
    value_type = float
    entity = Person
    label = "universal childcare entitlement hours per year"
    definition_period = YEAR
    unit = "hour"

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.universal_childcare_entitlement
        age = person("age", period)
        country = person.household("country", period)
        countries = country.possible_values
        in_England = country == countries.ENGLAND
        return where(in_England, p.hours.calc(age), 0)
