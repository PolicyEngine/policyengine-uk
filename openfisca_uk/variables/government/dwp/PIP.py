from openfisca_uk.model_api import *


class PIP(Variable):
    value_type = float
    entity = Person
    label = "Personal Independence Payment"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return add(person, period, ["PIP_M", "PIP_DL"])


class PIP_DL(Variable):
    value_type = float
    entity = Person
    label = "Personal Independence Payment (Daily Living)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("PIP_DL_reported", period)


class PIP_M(Variable):
    value_type = float
    entity = Person
    label = "Personal Independence Payment (Mobility)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("PIP_M_reported", period)


class PIP_DL_reported(Variable):
    value_type = float
    entity = Person
    label = "Personal Independence Payment (Daily Living) (reported)"
    definition_period = YEAR
    unit = "currency-GBP"


class PIP_M_reported(Variable):
    value_type = float
    entity = Person
    label = "Personal Independence Payment (Mobility) (reported)"
    definition_period = YEAR
    unit = "currency-GBP"
