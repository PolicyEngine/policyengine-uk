from policyengine_uk.model_api import *
from policyengine_uk.variables.misc.categories.lower_middle_or_higher import (
    LowerMiddleOrHigher,
)
from policyengine_uk.variables.misc.categories.lower_or_higher import (
    LowerOrHigher,
)
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory

label = "Disability"


class dla_sc_category(Variable):
    label = "DLA (Self-care) category"
    documentation = "If you receive the self-care component of Disability Living Allowance, you will be in one of the following categories: Lower, Middle, Higher. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerMiddleOrHigher
    default_value = LowerMiddleOrHigher.NONE

    def formula(person, period, parameters):
        dla_sc = parameters(period).gov.dwp.dla.self_care
        SAFETY_MARGIN = 0.1  # Survey reported values could be slightly below eligible values when they should be above due to data manipulation
        reported_weekly_dla_sc = (
            person("DLA_SC_reported", period) / WEEKS_IN_YEAR
        )
        return select(
            [
                reported_weekly_dla_sc >= dla_sc.higher * (1 - SAFETY_MARGIN),
                reported_weekly_dla_sc >= dla_sc.middle * (1 - SAFETY_MARGIN),
                reported_weekly_dla_sc >= dla_sc.lower * (1 - SAFETY_MARGIN),
                True,
            ],
            [
                LowerMiddleOrHigher.HIGHER,
                LowerMiddleOrHigher.MIDDLE,
                LowerMiddleOrHigher.LOWER,
                LowerMiddleOrHigher.NONE,
            ],
        )


class dla_m_category(Variable):
    label = "DLA (mobility) category"
    documentation = "If you receive the mobility component of Disability Living Allowance, you will be in one of the following categories: Lower, Higher. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = LowerOrHigher
    default_value = LowerOrHigher.NONE

    def formula(person, period, parameters):
        dla_m = parameters(period).gov.dwp.dla.mobility
        SAFETY_MARGIN = 0.1  # Survey reported values could be slightly below eligible values when they should be above due to data manipulation
        reported_weekly_dla_m = (
            person("DLA_M_reported", period) / WEEKS_IN_YEAR
        )
        return select(
            [
                reported_weekly_dla_m >= dla_m.higher * (1 - SAFETY_MARGIN),
                reported_weekly_dla_m >= dla_m.lower * (1 - SAFETY_MARGIN),
                True,
            ],
            [
                LowerOrHigher.HIGHER,
                LowerOrHigher.LOWER,
                LowerOrHigher.NONE,
            ],
        )


class pip_m_category(Variable):
    label = "PIP (mobility) category"
    documentation = "If you receive the mobility component of the Personal Independence Payment, you will be in one of the following categories: Standard or Enhanced. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = PIPCategory
    default_value = PIPCategory.NONE

    def formula(person, period, parameters):
        pip_m = parameters(period).gov.dwp.pip.mobility
        SAFETY_MARGIN = 0.1  # Survey reported values could be slightly below eligible values when they should be above due to data manipulation
        reported_weekly_pip_m = (
            person("PIP_M_reported", period) / WEEKS_IN_YEAR
        )
        return select(
            [
                reported_weekly_pip_m >= pip_m.enhanced * (1 - SAFETY_MARGIN),
                reported_weekly_pip_m >= pip_m.standard * (1 - SAFETY_MARGIN),
                True,
            ],
            [
                PIPCategory.ENHANCED,
                PIPCategory.STANDARD,
                PIPCategory.NONE,
            ],
        )


class pip_dl_category(Variable):
    label = "PIP (daily living) category"
    documentation = "If you receive the daily living component of the Personal Independence Payment, you will be in one of the following categories: Standard or Enhanced. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = PIPCategory
    default_value = PIPCategory.NONE

    def formula(person, period, parameters):
        pip_dl = parameters(period).gov.dwp.pip.daily_living
        SAFETY_MARGIN = 0.1  # Survey reported values could be slightly below eligible values when they should be above due to data manipulation
        reported_weekly_pip_dl = (
            person("PIP_DL_reported", period) / WEEKS_IN_YEAR
        )
        return select(
            [
                reported_weekly_pip_dl
                >= pip_dl.enhanced * (1 - SAFETY_MARGIN),
                reported_weekly_pip_dl
                >= pip_dl.standard * (1 - SAFETY_MARGIN),
                True,
            ],
            [
                PIPCategory.ENHANCED,
                PIPCategory.STANDARD,
                PIPCategory.NONE,
            ],
        )
