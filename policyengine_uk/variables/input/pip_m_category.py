from policyengine_uk.model_api import *
from policyengine_uk.utils.pip import pip_category
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class pip_m_category(Variable):
    label = "PIP (mobility) category"
    documentation = "If you receive the mobility component of the Personal Independence Payment, you will be in one of the following categories: Standard or Enhanced. If not, select None. Survey reported amounts should be converted to this category in the data pipeline. When not provided as input for the year, the category is derived from the person's latest `pip_m_points` for this or an earlier year against the points thresholds in `gov.dwp.pip.mobility.points_thresholds`. A category supplied for an earlier year carries forward instead, unless the person has points for a later year than that category."
    entity = Person
    definition_period = YEAR
    value_type = Enum
    possible_values = PIPCategory
    default_value = PIPCategory.NONE

    def formula(person, period, parameters):
        thresholds = parameters(period).gov.dwp.pip.mobility.points_thresholds
        return pip_category(person, period, thresholds, "m")
