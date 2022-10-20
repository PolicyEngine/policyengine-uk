from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class PIP_M_reported(Variable):
    value_type = float
    entity = Person
    label = "Disability Living Allowance (mobility) (reported)"
    definition_period = YEAR
    unit = GBP


class pip_m_category(Variable):
    label = "PIP (mobility) category"
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


class pip_m(Variable):
    label = "PIP (mobility)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        pip_m = parameters(period).gov.dwp.pip.mobility
        category = person("pip_m_category", period)
        return (
            select(
                [
                    category == PIPCategory.ENHANCED,
                    category == PIPCategory.STANDARD,
                    category == PIPCategory.NONE,
                ],
                [
                    pip_m.enhanced,
                    pip_m.standard,
                    0,
                ],
            )
            * WEEKS_IN_YEAR
        )
