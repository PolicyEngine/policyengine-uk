from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class age(Variable):
    value_type = float
    entity = Person
    label = u'The age of the person in years'
    definition_period = YEAR

class over_16(Variable):
    value_type = float
    entity = Person
    label = u'Whether the person is over 16'
    definition_period = YEAR
    
    def formula(person, period, parameters):
        return person("age", period) >= 16

class Gender(Enum):
    MALE = "Male"
    FEMALE = "Female"

class gender(Variable):
    value_type = Enum
    possible_values = Gender
    default_value = Gender.MALE
    entity = Person
    label = u'Gender of the person'
    definition_period = YEAR

class household_head(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is the head-of-household'
    definition_period = YEAR

class benunit_head(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is the head-of-family'
    definition_period = YEAR