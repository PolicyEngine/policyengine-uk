from policyengine_uk.model_api import *


class targeted_childcare_entitlement(Variable):
    value_type = float
    entity = BenUnit
    label = "targeted childcare entitlement amount per year"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe
        ages = benunit.members("age", period)
        hours = benunit.members("targeted_childcare_entitlement_hours", period)
        return benunit.sum(hours * p.childcare_funding_rate.calc(ages))
