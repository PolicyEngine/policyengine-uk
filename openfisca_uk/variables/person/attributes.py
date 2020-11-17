from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class index(Variable):
    value_type = float
    entity = Person
    label = u'Unique index for simulation purposes'
    definition_period = ETERNITY

class age(Variable):
    value_type = float
    entity = Person
    label = u'Age in years'
    definition_period = YEAR

class is_SP_age(Variable):
    value_type = float
    entity = Person
    label = u'Whether over the State Pension Age'
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period) >= 65) + (person("state_pension", period) > 0)

class is_benunit_head(Variable):
    value_type = float
    entity = Person
    label = u'Whether the head of the benefit unit'
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return person("index", period) == aggr_max(person.benunit, period, ["index"])