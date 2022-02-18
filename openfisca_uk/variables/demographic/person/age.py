from openfisca_uk.model_api import *


class age(Variable):
    value_type = int
    entity = Person
    label = "Age"
    unit = "year"
    documentation = "The age of the person in years"
    definition_period = YEAR

    def formula(person, period, parameters):
        ADULT_DEFAULT_AGE = 18
        CHILD_DEFAULT_AGE = 10
        is_adult = person.benunit.members_role == BenUnit.ADULT
        return where(is_adult, ADULT_DEFAULT_AGE, CHILD_DEFAULT_AGE)


class birth_year(Variable):
    value_type = int
    entity = Person
    label = "Birth year"
    documentation = "The year in which this person was born"
    definition_period = YEAR

    def formula(person, period):
        return period.start.year - person("age", period)


class birth_date(Variable):
    label = "Date of birth"
    documentation = "The date on which this person was born"
    entity = Person
    definition_period = ETERNITY
    value_type = date

    def formula(person, period):
        birth_years = person("birth_year", period)
        return np.array([date(year, 1, 1) for year in birth_years])


class over_16(Variable):
    label = "Over 16"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        return person("age", period) >= 16
