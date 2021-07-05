from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class person_id(Variable):
    value_type = float
    entity = Person
    label = u"ID for the person"
    definition_period = YEAR


class people(Variable):
    value_type = float
    entity = Person
    label = u"Variable holding people"
    definition_period = YEAR
    default_value = 1


class person_weight(Variable):
    value_type = float
    entity = Person
    label = u"Weight factor for the person"
    definition_period = YEAR
    default_value = 1


class age(Variable):
    value_type = float
    entity = Person
    label = u"The age of the person in years"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period
    default_value = 18


class birth_year(Variable):
    value_type = float
    entity = Person
    label = u"The birth year of the person"
    definition_period = YEAR

    def formula(person, period, parameters):
        return datetime.now().year - person("age", period)


class over_16(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is over 16"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) >= 16


class is_adult(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is an adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) >= 18


class is_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is a child"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) < 18


class in_FE(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is in Further Education"
    definition_period = YEAR
    set_input = set_input_dispatch_by_period


class in_HE(Variable):
    value_type = bool
    entity = Person
    label = u"label"
    definition_period = YEAR
    reference = "Whether this person is in Higher Education"
    set_input = set_input_dispatch_by_period


class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"


class gender(Variable):
    value_type = Enum
    possible_values = Gender
    default_value = Gender.MALE
    entity = Person
    label = u"Gender of the person"
    definition_period = ETERNITY


class is_male(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is male"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("gender", period) == Gender.MALE


class is_female(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is female"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("gender", period) == Gender.FEMALE


class is_household_head(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is the head-of-household"
    definition_period = YEAR


class is_benunit_head(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is the head-of-family"
    definition_period = YEAR


class in_social_housing(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person lives in social housing"
    definition_period = YEAR

    def formula(person, period, parameters):
        tenure = person.household("tenure_type", period.this_year)
        tenures = tenure.possible_values
        social = is_in(tenure, tenures.RENT_FROM_COUNCIL, tenures.RENT_FROM_HA)
        return social


class is_WA_adult(Variable):
    value_type = bool
    entity = Person
    label = u"Whether is a working-age adult"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("is_adult", period) * not_(person("is_SP_age", period))


class is_young_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is under 14"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period.this_year) < 14


class age_under_18(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is under age 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) < 18


class age_18_64(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is age 18 to 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        return (age >= 18) & (age <= 64)


class age_over_64(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is over age 64"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("age", period) > 64


class is_older_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is over 14 but under 18"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period) >= 14) * (person("age", period) < 18)
