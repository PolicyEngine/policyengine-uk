from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class person_weight(Variable):
    value_type = float
    entity = Person
    label = u'Weight factor for the person'
    definition_period = YEAR

class age(Variable):
    value_type = float
    entity = Person
    label = u'The age of the person in years'
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

class over_16(Variable):
    value_type = float
    entity = Person
    label = u'Whether the person is over 16'
    definition_period = YEAR
    
    def formula(person, period, parameters):
        return person("age", period) >= 16

class in_FE(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is in Further Education'
    definition_period = YEAR
    set_input = set_input_dispatch_by_period

class in_HE(Variable):
    value_type = bool
    entity = Person
    label = u'label'
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
    label = u'Gender of the person'
    definition_period = ETERNITY

class is_household_head(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is the head-of-household'
    definition_period = YEAR

class is_benunit_head(Variable):
    value_type = bool
    entity = Person
    label = u'Whether this person is the head-of-family'
    definition_period = YEAR