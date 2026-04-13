from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region


class MaintenanceLoanLivingArrangement(Enum):
    LIVING_WITH_PARENTS = "Living with parents"
    AWAY_OUTSIDE_LONDON = "Living away from home and studying outside London"
    AWAY_IN_LONDON = "Living away from home and studying in London"


class maintenance_loan_living_arrangement(Variable):
    value_type = Enum
    possible_values = MaintenanceLoanLivingArrangement
    default_value = MaintenanceLoanLivingArrangement.AWAY_OUTSIDE_LONDON
    entity = Person
    label = "Maintenance loan living arrangement"
    documentation = (
        "Student Finance England living-arrangement category. "
        "By default this is proxied from current household composition and region, "
        "but it can be set explicitly in simulations."
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        is_household_head = person("is_household_head", period)
        household = person.household
        region = household("region", period)
        eldest_age_in_household = household.max(household.members("age", period))

        living_with_parents_proxy = ~is_household_head & (
            eldest_age_in_household >= age + 15
        )
        away_in_london = region == Region.LONDON

        return select(
            [living_with_parents_proxy, away_in_london],
            [
                MaintenanceLoanLivingArrangement.LIVING_WITH_PARENTS,
                MaintenanceLoanLivingArrangement.AWAY_IN_LONDON,
            ],
            default=MaintenanceLoanLivingArrangement.AWAY_OUTSIDE_LONDON,
        )
