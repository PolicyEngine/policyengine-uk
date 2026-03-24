from policyengine_uk.model_api import *


class council_tax_reduction_relevant_income_based_benefit(Variable):
    value_type = bool
    entity = BenUnit
    label = "CTR claimant has an income-based passporting benefit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return (
            add(benunit, period, ["income_support", "jsa_income", "esa_income"]) > 0
        )
