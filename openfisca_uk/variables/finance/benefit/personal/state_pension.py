from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class is_SP_age(Variable):
    value_type = float
    entity = Person
    label = u"Whether the person is State Pension Age"
    definition_period = YEAR
    reference = ""

    def formula(person, period, parameters):
        return (
            person("age", period)
            >= parameters(period).benefit.state_pension.default_age
        )


class state_pension(Variable):
    value_type = float
    entity = Person
    label = u"Income from the State Pension"
    definition_period = WEEK

    def formula(person, period, parameters):
        return person("state_pension_reported", period)


class state_pension_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported income from the State Pension"
    definition_period = WEEK
