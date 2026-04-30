from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_middle_or_higher import (
    LowerMiddleOrHigher,
)


class dla_sc_category(Variable):
    label = "DLA (Self-care) category"
    documentation = "If you receive the self-care component of Disability Living Allowance, you will be in one of the following categories: Lower, Middle, Higher. If not, select None. Survey reported amounts should be converted to this category in the data pipeline."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerMiddleOrHigher
    default_value = LowerMiddleOrHigher.NONE
