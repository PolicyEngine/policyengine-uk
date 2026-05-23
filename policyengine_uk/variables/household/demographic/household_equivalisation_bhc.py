from policyengine_uk.model_api import *


class household_equivalisation_bhc(Variable):
    value_type = float
    entity = Household
    label = "Equivalisation factor to account for household composition, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        scale = parameters(period).household.demographic.equiv.bhc
        count_other_adults = max_(
            household.sum(household.members("is_adult", period)) - 1, 0
        )
        count_young_children = household.sum(
            household.members("is_young_child", period)
        )
        count_older_children = household.sum(
            household.members("is_older_child", period)
        )
        return (
            scale.first_adult
            + scale.second_adult * count_other_adults
            + scale.child_over_14 * count_older_children
            + scale.child_under_14 * count_young_children
        )
