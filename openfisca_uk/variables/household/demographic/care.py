from openfisca_uk.model_api import *


class is_carer_for_benefits(Variable):
    value_type = bool
    entity = Person
    label = "Whether this person is a carer for benefits purposes"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("receives_carers_allowance", period)


class benunit_has_carer(Variable):
    value_type = bool
    entity = BenUnit
    label = "Benefit unit has a carer"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("num_carers", period) > 0


class num_carers(Variable):
    value_type = int
    entity = BenUnit
    label = "Number of carers in the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["is_carer_for_benefits"])


class carer_premium(Variable):
    value_type = float
    entity = BenUnit
    label = "Carer premium"
    definition_period = YEAR
    reference = (
        "The Social Security Amendment (Carer Premium) Regulations 2002"
    )
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        carers = benunit("num_carers", period.this_year)
        CP = parameters(period).benefit.carer_premium
        weekly_premium = select(
            [carers == 0, carers == 1, carers == 2],
            [0, CP.single, CP.couple],
        )
        return weekly_premium * WEEKS_IN_YEAR
