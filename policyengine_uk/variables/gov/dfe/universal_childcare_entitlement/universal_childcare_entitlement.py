from policyengine_uk.model_api import *


class universal_childcare_entitlement(Variable):
    value_type = float
    entity = BenUnit
    label = "universal childcare entitlement amount per year"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dfe
        is_eligible = benunit.members(
            "universal_childcare_entitlement_eligible", period
        )
        ages = benunit.members("age", period)
        hours = where(is_eligible, p.universal_childcare_entitlement.hours, 0)
        return benunit.sum(hours * p.childcare_funding_rate.calc(ages))
