from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

# Input from FRS


class person_id(Variable):
    value_type = int
    entity = Person
    label = u"ID of the person"
    definition_period = ETERNITY


class age(Variable):
    value_type = float
    entity = Person
    label = u"Age in years"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period


class is_adult(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is an adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) >= 18


class is_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is a child"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 18


class is_benunit_head(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the head of the benefit unit"
    definition_period = ETERNITY


class is_household_head(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the head of the household"
    definition_period = ETERNITY


class hours(Variable):
    value_type = float
    entity = Person
    label = u"Hours worked per week"
    definition_period = WEEK
    set_input = set_input_divide_by_period


class care_hours_given(Variable):
    value_type = float
    entity = Person
    label = u"Hours spent per week providing care"
    definition_period = WEEK


class care_hours_recieved(Variable):
    value_type = float
    entity = Person
    label = u"Hours spent per week providing care"
    definition_period = WEEK


class adult_weight(Variable):
    value_type = float
    entity = Person
    label = u"Weight of the adult"
    definition_period = ETERNITY


class is_married(Variable):
    value_type = float
    entity = Person
    label = u"Whether is married"
    definition_period = YEAR


# Derived variables


class weekly_hours(Variable):
    value_type = float
    entity = Person
    label = u"Average weekly hours for the year"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("hours", period, options=[ADD]) / 52


class is_young_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is under 14"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 14


class is_older_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is over 14 but under 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period.this_year) >= 14) * (
            person("age", period.this_year) < 18
        )


class is_SP_age(Variable):
    value_type = float
    entity = Person
    label = u"Whether over the State Pension Age"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

    def formula(person, period, parameters):
        return (person("age", period.this_year) >= 65) + (
            person("state_pension", period) > 0
        )


class is_WA_adult(Variable):
    value_type = float
    entity = Person
    label = u"Whether is a working-age adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("is_adult", period) * not_(person("is_SP_age", period))


class living_in_social_housing(Variable):
    value_type = bool
    entity = Person
    label = u"Whether is living in social housing"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person.household("is_social", period)


class living_in_shared_accomodation(Variable):
    value_type = bool
    entity = Person
    label = u"Whether is living in social housing"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person.household("is_shared", period)


class person_region(Variable):
    value_type = int
    entity = Person
    label = u"This person's region"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person.household("region", period)


class is_renting(Variable):
    value_type = float
    entity = Person
    label = u"Whether is renting"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person.household("is_rented", period)


class num_bedrooms_in_household(Variable):
    value_type = float
    entity = Person
    label = u"The number of bedrooms in this person's household"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person.household("num_bedrooms", period)

class age_under_18(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is under age 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 18


class age_18_64(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is age 18 to 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period.this_year)
        return (age >= 18) & (age <= 64)


class age_over_64(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is over age 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) > 64


class is_older_child(Variable):
    value_type = bool
    