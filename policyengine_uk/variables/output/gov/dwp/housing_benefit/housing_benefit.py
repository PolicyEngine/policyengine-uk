from policyengine_uk.model_api import *


class housing_benefit(Variable):
    label = "Housing Benefit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    defined_for = "would_claim_housing_benefit"

    def formula(benunit, period, parameters):
        housing_benefit_entitlement = benunit(
            "housing_benefit_pre_benefit_cap", period
        )
        benefit_cap_reduction = benunit("benefit_cap_reduction", period)
        return max_(0, housing_benefit_entitlement - benefit_cap_reduction)
