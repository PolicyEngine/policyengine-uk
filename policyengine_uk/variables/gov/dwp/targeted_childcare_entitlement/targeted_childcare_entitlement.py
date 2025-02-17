from policyengine_uk.model_api import *


class targeted_childcare_entitlement(Variable):
    value_type = float
    entity = BenUnit
    label = "targeted childcare entitlement amount per year"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        hours = benunit.members("targeted_childcare_entitlement_hours", period)
        p = parameters(period).gov.dwp.targeted_childcare_entitlement
        individual_subsidy = hours * p.funding_rate
        return benunit.sum(individual_subsidy)
