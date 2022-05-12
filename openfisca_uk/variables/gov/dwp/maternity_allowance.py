from openfisca_uk.model_api import *


class maternity_allowance_reported(Variable):
    value_type = float
    entity = Person
    label = "Maternity allowance"
    definition_period = YEAR
    unit = GBP


@uprated(by="uprating.september_cpi")
class maternity_allowance(Variable):
    label = "Maternity Allowance"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        return person("maternity_allowance_reported", period)


class ssmg_reported(Variable):
    label = "Sure Start Maternity Grant (reported)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP


class ssmg(Variable):
    label = "Sure Start Maternity Grant"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        return person("ssmg_reported", period)
