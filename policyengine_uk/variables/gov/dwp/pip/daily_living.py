from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class PIP_DL_reported(Variable):
    value_type = float
    entity = Person
    label = "PIP (self-care) (reported)"
    definition_period = YEAR
    unit = GBP


class pip_dl_category(Variable):
    label = "PIP (daily living) category"
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


class pip_dl(Variable):
    label = "PIP (daily living)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        pip_dl = parameters(period).gov.dwp.pip.daily_living
        category = person("pip_dl_category", period)
        return (
            select(
                [
                    category == PIPCategory.ENHANCED,
                    category == PIPCategory.STANDARD,
                    category == PIPCategory.NONE,
                ],
                [
                    pip_dl.enhanced,
                    pip_dl.standard,
                    0,
                ],
            )
            * WEEKS_IN_YEAR
        )


class receives_enhanced_pip_dl(Variable):
    label = "Receives enhanced PIP (daily living)"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        return person("pip_dl_category", period) == PIPCategory.ENHANCED
