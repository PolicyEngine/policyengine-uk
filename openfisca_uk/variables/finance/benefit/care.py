from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class is_carer_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is a carer for benefits purposes"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("receives_carers_allowance", period)


class benunit_has_carer(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Benefit unit has a carer"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("num_carers", period) > 0


class num_carers(Variable):
    value_type = int
    entity = BenUnit
    label = u"Number of carers in the family"
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
