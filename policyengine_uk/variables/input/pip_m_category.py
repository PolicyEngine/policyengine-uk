from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class pip_m_category(Variable):
    label = "PIP (mobility) category"
    documentation = "If you receive the mobility component of the Personal Independence Payment, you will be in one of the following categories: Standard or Enhanced. If not, select None."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = PIPCategory
    default_value = PIPCategory.NONE

    def formula(person, period, parameters):
        pip_m = parameters(period).baseline.gov.dwp.pip.mobility
        SAFETY_MARGIN = 0.1  # Survey reported values could be slightly below eligible values when they should be above due to data manipulation
        reported_weekly_pip_m = (
            person("pip_m_reported", period) / WEEKS_IN_YEAR
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
