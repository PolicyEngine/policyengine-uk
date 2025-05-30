from policyengine_uk.variables.household.demographic.household import (

class relation_type(Variable):
    value_type = Enum
    entity = BenUnit
    default_value = RelationType.SINGLE
    possible_values = RelationType
    label = "Whether single or a couple"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return where(
            benunit.sum(benunit.members("is_adult", period)) == 1,
            RelationType.SINGLE,
            RelationType.COUPLE,
        )
