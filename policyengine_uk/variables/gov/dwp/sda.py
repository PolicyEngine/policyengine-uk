from policyengine_uk.model_api import *


class sda(Variable):
    value_type = float
    entity = Person
    label = "Severe Disablement Allowance"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        reported = person("SDA_reported", period) > 0
        # SDA recipients receive a basic rate, and potentially
        # an age-related addition. We assume they receive the highest
        # age-related addition.
        rate = parameters(period).gov.dwp.sda.maximum
        return reported * rate * WEEKS_IN_YEAR


class SDA_reported(Variable):
    value_type = float
    entity = Person
    label = "Severe Disablement Allowance (reported)"
    definition_period = YEAR
    unit = GBP
