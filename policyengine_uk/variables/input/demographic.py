from policyengine_uk.model_api import *

label = "Demographic"
description = "Demographic variables."


class age(Variable):
    value_type = float
    entity = Person
    label = "age"
    unit = "year"
    value_type = float
    documentation = "Age in years."
    definition_period = YEAR
    quantity_type = STOCK
    default_value = 40


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class gender(Variable):
    label = "gender"
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = Gender
    default_value = Gender.MALE

class household_weight(Variable):
    label = "household weight"
    documentation = "Number of households this observation represents."
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "household"
    quantity_type = STOCK
    default_value = 1


class person_weight(Variable):
    label = "person weight"
    documentation = "Number of people this observation represents."
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = "person"
    quantity_type = STOCK
    default_value = 1


class benefit_unit_weight(Variable):
    label = "benefit unit weight"
    documentation = "Number of families this observation represents."
    entity = BenefitUnit
    definition_period = YEAR
    value_type = float
    unit = "benefit unit"
    quantity_type = STOCK
    default_value = 1


class person_id(Variable):
    label = "person ID"
    entity = Person
    definition_period = YEAR
    value_type = int
    quantity_type = STOCK
    default_value = 1


class benefit_unit_id(Variable):
    label = "benefit unit ID"
    entity = BenefitUnit
    definition_period = YEAR
    value_type = int
    quantity_type = STOCK
    default_value = 1


class household_id(Variable):
    label = "household ID"
    entity = Household
    definition_period = YEAR
    value_type = int
    quantity_type = STOCK
    default_value = 1

class person_benefit_unit_id(Variable):
    label = "person's benefit unit ID"
    entity = Person
    definition_period = YEAR
    value_type = int
    quantity_type = STOCK
    default_value = 1

class person_household_id(Variable):
    label = "household's benefit unit ID"
    entity = Household
    definition_period = YEAR
    value_type = int
    quantity_type = STOCK
    default_value = 1




