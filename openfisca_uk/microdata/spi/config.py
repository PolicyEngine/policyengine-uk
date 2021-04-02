from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *

class FACT(Variable):
    value_type = float
    entity = Person
    label = u'Weight for people'
    definition_period = YEAR

class PAY(Variable):
    value_type = float
    entity = Person
    label = u"Pay from employment net of benefits and foreign earnings"
    definition_period = YEAR

class earnings(Variable):
    value_type = float
    entity = Person
    label = u"Gross earnings from employment"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("PAY", period)


SPI_variables = [PAY, FACT]
input_variables = [earnings]


class from_SPI(Reform):
    def apply(self):
        for var in SPI_variables:
            self.add_variable(var)
        for var in input_variables:
            self.update_variable(var)
