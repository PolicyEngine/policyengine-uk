from policyengine_uk.model_api import *


class universal_childcare_entitlement(Variable):
    value_type = float
    entity = BenUnit
    label = "universal childcare entitlement amount per year"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        hours = benunit.members(
            "universal_childcare_entitlement_hours", period
        )
        ages = benunit.members("age", period)
        p = parameters(period).gov.dfe
        return benunit.sum(hours * p.childcare_funding_rate.calc(ages))
