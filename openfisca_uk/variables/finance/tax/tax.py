from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class tax(Variable):
    value_type = float
    entity = Person
    label = u"Total tax"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("income_tax", period) + person(
            "national_insurance", period
        )


class benunit_tax(Variable):
    value_type = float
    entity = BenUnit
    label = u"Benefit unit tax paid"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("tax", period))


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
