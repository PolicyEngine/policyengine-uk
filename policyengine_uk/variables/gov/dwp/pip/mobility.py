from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class PIP_M_reported(Variable):
    value_type = float
    entity = Person
    label = "Disability Living Allowance (mobility) (reported)"
    definition_period = YEAR
    unit = GBP


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
