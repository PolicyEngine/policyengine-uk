from policyengine_uk.model_api import *


class MealsIncludedInRent(Enum):
    NONE = "No meals"
    BREAKFAST_ONLY = "Breakfast only"
    FEWER_THAN_THREE_A_DAY = "Fewer than three meals a day"
    AT_LEAST_THREE_A_DAY = "At least three meals a day"


class meals_included_in_rent(Variable):
    value_type = Enum
    possible_values = MealsIncludedInRent
    default_value = MealsIncludedInRent.NONE
    entity = BenUnit
    label = "Meals included in the family's rent"
    documentation = (
        "Meals the family's rent pays for, as for a boarder. The Family "
        "Resources Survey records whether someone is a boarder but not how "
        "many meals they get."
    )
    definition_period = YEAR
