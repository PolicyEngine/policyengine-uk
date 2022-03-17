from openfisca_uk.model_api import *


class DLA(Variable):
    value_type = float
    entity = Person
    label = "Disability Living Allowance"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return add(person, period, ["DLA_M", "DLA_SC"])


class DLA_M(Variable):
    value_type = float
    entity = Person
    label = "Disability Living Allowance (mobility component)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("DLA_M_reported", period)


class DLA_SC(Variable):
    value_type = float
    entity = Person
    label = "Disability Living Allowance (self-care)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        return person("DLA_SC_reported", period)


class DLA_SC_middle_plus(Variable):
    value_type = bool
    entity = Person
    label = "Receives at least DLA (self-care) middle rate"
    definition_period = YEAR

    def formula(person, period, parameters):
        DLA_SC = parameters(period).benefit.DLA.self_care
        return person("DLA_SC", period) >= DLA_SC.middle


class DLA_M_reported(Variable):
    value_type = float
    entity = Person
    label = "Disability Living Allowance (mobility component) (reported)"
    definition_period = YEAR
    unit = "currency-GBP"


class DLA_SC_reported(Variable):
    value_type = float
    entity = Person
    label = "Disability Living Allowance (self-care) (reported)"
    definition_period = YEAR
    unit = "currency-GBP"
