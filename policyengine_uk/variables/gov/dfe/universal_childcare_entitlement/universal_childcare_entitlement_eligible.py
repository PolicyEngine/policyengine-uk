from policyengine_uk.model_api import *


class universal_childcare_entitlement_eligible(Variable):
    value_type = bool
    entity = Person
    label = "eligible for universal childcare entitlement"
    definition_period = YEAR

    def formula(person, period, parameters):
        country = person.household("country", period)
        countries = country.possible_values
        in_england = country == countries.ENGLAND

        age = person("age", period)
        p = parameters(period).gov.dfe.universal_childcare_entitlement
        meets_min_age = age >= p.min_age
        not_compulsory_age = ~person("is_of_compulsory_school_age", period)

        return in_england & meets_min_age & not_compulsory_age
