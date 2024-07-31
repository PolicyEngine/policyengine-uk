from policyengine_uk.model_api import *


class PIPCategory(Enum):
    STANDARD = "Standard"
    ENHANCED = "Enhanced"
    NONE = "None"


class dla_sc_category(Variable):
    label = "DLA (Self-care) category"
    documentation = "If you receive the self-care component of Disability Living Allowance, you will be in one of the following categories: Lower, Middle, Higher. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerMiddleOrHigher
    default_value = LowerMiddleOrHigher.NONE


class dla_m_category(Variable):
    label = "DLA (mobility) category"
    documentation = "If you receive the mobility component of Disability Living Allowance, you will be in one of the following categories: Lower, Higher. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerOrHigher
    default_value = LowerOrHigher.NONE


class pip_m_category(Variable):
    label = "PIP (mobility) category"
    documentation = "If you receive the mobility component of the Personal Independence Payment, you will be in one of the following categories: Standard or Enhanced. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = PIPCategory
    default_value = PIPCategory.NONE


class pip_dl_category(Variable):
    label = "PIP (daily living) category"
    documentation = "If you receive the daily living component of the Personal Independence Payment, you will be in one of the following categories: Standard or Enhanced. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = PIPCategory
    default_value = PIPCategory.NONE
