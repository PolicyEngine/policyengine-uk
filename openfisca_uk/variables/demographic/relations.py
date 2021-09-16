from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class person_benunit_id(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class person_household_id(Variable):
    value_type = float
    entity = Person
    definition_period = YEAR


class role(Variable):
    value_type = str
    entity = Person
    definition_period = YEAR


class B_benunit_id(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR


class B_household_id(Variable):
    value_type = float
    entity = BenUnit
    definition_period = YEAR


class H_household_id(Variable):
    value_type = float
    entity = Household
    definition_period = YEAR
