from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class is_carer_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is a carer for benefits purposes"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("carers_allowance", period) > 0


class num_carers(Variable):
    value_type = int
    entity = BenUnit
    label = u"The number of carers for benefits purposes in the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_carer_for_benefits", period))


class carer_premium(Variable):
    value_type = float
    entity = BenUnit
    label = u"Carer premium"
    definition_period = YEAR
    reference = (
        "The Social Security Amendment (Carer Premium) Regulations 2002"
    )

    def formula(benunit, period, parameters):
        carers = benunit("num_carers", period.this_year)
        CP = parameters(period).benefit.carer_premium
        return (
            select(
                [carers == 0, carers == 1, carers == 2],
                [0, CP.single, CP.couple],
            )
            * WEEKS_IN_YEAR
        )
