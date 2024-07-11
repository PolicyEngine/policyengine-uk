from policyengine_uk.model_api import *


class uc_minimum_income_floor(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit minimum income floor"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        expected_hours = parameters(
            period
        ).gov.dwp.universal_credit.work_requirements.default_expected_hours
        return person("minimum_wage", period) * expected_hours * WEEKS_IN_YEAR
