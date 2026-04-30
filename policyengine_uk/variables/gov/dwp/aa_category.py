from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_or_higher import (
    LowerOrHigher,
)


class aa_category(Variable):
    label = "Attendance Allowance category"
    documentation = "If you receive Attendance Allowance, you will be in one of the following categories: Lower or Higher. If not, select None. Survey reported amounts should be converted to this category in the data pipeline."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerOrHigher
    default_value = LowerOrHigher.NONE
