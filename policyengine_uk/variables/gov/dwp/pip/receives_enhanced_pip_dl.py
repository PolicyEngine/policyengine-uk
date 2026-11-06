from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.dwp.pip.pip import PIPCategory


class receives_enhanced_pip_dl(Variable):
    label = "Receives enhanced PIP (daily living)"
    entity = Person
    definition_period = YEAR
    value_type = bool

    def formula(person, period, parameters):
        # As in pip_dl, no award is paid below the minimum age.
        old_enough = person("age", period) >= parameters(period).gov.dwp.pip.min_age
        enhanced = person("pip_dl_category", period) == PIPCategory.ENHANCED
        return enhanced & old_enough
