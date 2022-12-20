from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class PIP_DL_reported(Variable):
    value_type = float
    entity = Person
    label = "PIP (self-care) (reported)"
    definition_period = YEAR
    unit = GBP


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
