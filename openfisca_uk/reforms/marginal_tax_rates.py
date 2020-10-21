from openfisca_core.model_api import *
from openfisca_uk.entities import *


class taxed_means_tested_bonus(Variable):
    value_type = float
    entity = Person
    label = u"Small bonus on earnings to simulate a MTR"
    definition_period = ETERNITY

    def formula(person, period, parameters):
        return 25 * (1 - person("is_child", period))


class small_earnings_increase(Reform):
    def apply(self):
        self.update_variable(taxed_means_tested_bonus)
