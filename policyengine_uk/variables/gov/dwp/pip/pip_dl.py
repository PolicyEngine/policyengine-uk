from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class pip_dl(Variable):
    label = "PIP (daily living)"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        p = parameters(period).gov.dwp.pip.daily_living
        category = person("pip_dl_category", period)
        return (
            select(
                [
                    category == PIPCategory.ENHANCED,
                    category == PIPCategory.STANDARD,
                    category == PIPCategory.NONE,
                ],
                [
                    p.enhanced,
                    p.standard,
                    0,
                ],
            )
            * WEEKS_IN_YEAR
        )
