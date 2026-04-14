from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.geography import Region
import numpy as np


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
        in_higher_education = person("maintenance_loan_in_higher_education", period)
        has_sponsor = person("maintenance_loan_has_sponsor", period)
        is_household_head = person("is_household_head", period)
        is_couple = person.benunit("is_couple", period)
        is_parent = person("is_parent", period)
        tenure_holder = person.household.get_holder("tenure_type")
        has_explicit_tenure = (
            tenure_holder.get_array(period) is not None
            or tenure_holder.get_array(period.last_year) is not None
        )
        is_renting = (
            person.benunit("benunit_is_renting", period)
            if has_explicit_tenure
            else np.zeros_like(has_sponsor, dtype=bool)
        )
        region = person.household("region", period)

        living_with_parents_proxy = (
            in_higher_education
            & has_sponsor
            & np.logical_not(is_household_head)
            & np.logical_not(is_couple)
            & np.logical_not(is_parent)
            & np.logical_not(is_renting)
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
