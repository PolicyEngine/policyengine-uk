from policyengine_uk.model_api import *


class household_equivalisation_ahc(Variable):
    value_type = float
    entity = Household
    label = "Equivalisation factor to account for household composition, after housing costs"
    documentation = (
        "The HBAI modified OECD equivalence scale (AHC): a weight for the first "
        "adult, a weight for each other adult, and weights for dependent "
        "children under 14 and aged 14 or over. Adults and dependent children "
        "follow the HBAI definitions."
    )
    definition_period = YEAR
    reference = "https://www.gov.uk/government/statistics/households-below-average-income-for-financial-years-ending-1995-to-2025/households-below-average-income-background-information-and-methodology-report-fye-2025#equivalisation-1"

    def formula(household, period, parameters):
        scale = parameters(period).household.demographic.equiv.ahc
        count_other_adults = max_(
            household.sum(household.members("is_hbai_adult", period)) - 1, 0
        )
        count_young_children = household.sum(
            household.members("is_hbai_child_under_14", period)
        )
        count_older_children = household.sum(
            household.members("is_hbai_child_aged_14_or_over", period)
        )
        return (
            scale.first_adult
            + scale.second_adult * count_other_adults
            + scale.child_over_14 * count_older_children
            + scale.child_under_14 * count_young_children
        )
