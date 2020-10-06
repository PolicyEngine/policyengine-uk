from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

# Input variables


class is_male(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is male"
    definition_period = ETERNITY


class is_head(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is the head of the benefit unit"
    definition_period = ETERNITY


class is_state_pension_age(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is State Pension age"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        claiming_pension = person("state_pension_reported", period) > 0
        return claiming_pension + (1 - claiming_pension) * (
            person("age", period) >= 65
        )


class disabled(Variable):
    value_type = bool
    entity = Person
    label = u"Whether disabled"
    definition_period = ETERNITY


class adult_weight(Variable):
    value_type = float
    entity = Person
    label = u"FRS weighting of the person if they are an adult, 0 if a child (none provided by the FRS)"
    definition_period = ETERNITY


class hours_worked(Variable):
    value_type = float
    entity = Person
    label = u"Total hours worked per week"
    definition_period = ETERNITY


class age(Variable):
    value_type = int
    entity = Person
    label = u"Age of the person"
    definition_period = ETERNITY


class JSA_contrib_eligible(Variable):
    value_type = float
    entity = Person
    label = u"Whether the person is in receipt of contributory JSA"
    definition_period = ETERNITY


class hours_worked(Variable):
    value_type = float
    entity = Person
    label = u"Total hours worked per week"
    definition_period = ETERNITY


# Derived variables


class is_young_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is under 14"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("age", period) < 14


class is_older_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is over 14 but under 18"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return (person("age", period) >= 14) * (person("age", period) < 18)


class is_CTC_child_limit_exempt(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the child was born after 2017 and therefore exempt from the two-child limit for Child Tax Credit"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return (person("age", period) >= 3) * (1 - person("is_adult", period))


class is_senior(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is over retirement age"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("age", period) >= 65


class is_adult(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is working age"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return (person("age", period) >= 18) * (person("age", period) < 65)


class is_child(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person is under working age"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("age", period) < 18
