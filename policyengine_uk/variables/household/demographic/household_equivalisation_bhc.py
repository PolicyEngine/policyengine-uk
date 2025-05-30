from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class household_equivalisation_bhc(Variable):
    value_type = float
    entity = Household
    label = "Equivalisation factor to account for household composition, before housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
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
            0.67
            + 0.33 * count_other_adults
            + 0.33 * count_older_children
            + 0.2 * count_young_children
        )
