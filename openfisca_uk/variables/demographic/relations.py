from openfisca_uk.model_api import *


class person_benunit_id(Variable):
    value_type = float
    label = "Person's benefit unit ID"
    entity = Person
    definition_period = YEAR


class person_household_id(Variable):
    value_type = float
    label = "Person's household ID"
    entity = Person
    definition_period = YEAR


class role(Variable):
    value_type = str
    label = "Role (adult/child)"
    entity = Person
    definition_period = YEAR
