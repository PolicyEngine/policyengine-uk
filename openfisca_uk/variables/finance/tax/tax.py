from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class tax(Variable):
    value_type = float
    entity = Person
    label = u"Total tax liability"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("income_tax", period) + person(
            "national_insurance", period
        )


class tax_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported tax paid"
    definition_period = YEAR


class tax_modelling(Variable):
    value_type = float
    entity = Person
    label = u"Difference between reported and imputed tax liabilities"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("tax", period) - person("tax_reported", period)
