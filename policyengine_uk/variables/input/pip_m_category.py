from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class pip_m_category(Variable):
    label = "PIP (mobility) category"
    documentation = "If you receive the mobility component of the Personal Independence Payment, you will be in one of the following categories: Standard or Enhanced. If not, select None. Survey reported amounts should be converted to this category in the data pipeline. When not provided as input, the category is derived from `pip_m_points` against the points thresholds in `gov.dwp.pip.mobility.points_thresholds`."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = PIPCategory
    default_value = PIPCategory.NONE

    def formula(person, period, parameters):
        points = person("pip_m_points", period)
        thresholds = parameters(period).gov.dwp.pip.mobility.points_thresholds
        return select(
            [
                points >= thresholds.enhanced,
                points >= thresholds.standard,
                points < thresholds.standard,
            ],
            [
                PIPCategory.ENHANCED,
                PIPCategory.STANDARD,
                PIPCategory.NONE,
            ],
        )
