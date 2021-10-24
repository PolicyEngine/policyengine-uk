from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class person_benunit_id(Variable):
    value_type = float
    label = u"Person's benefit unit ID"
    entity = Person
    definition_period = YEAR


class person_household_id(Variable):
    value_type = float
    label = u"Person's household ID"
    entity = Person
    definition_period = YEAR


class role(Variable):
    value_type = str
    label = u"Role (adult/child)"
    entity = Person
    definition_period = YEAR
