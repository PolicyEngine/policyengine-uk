from policyengine_uk.model_api import *


class ssmg(Variable):
    label = "Sure Start Maternity Grant"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(person, period, parameters):
        reported_receipt = person("ssmg_reported", period) > 0
        return reported_receipt * parameters(period).gov.dwp.ssmg.rate
