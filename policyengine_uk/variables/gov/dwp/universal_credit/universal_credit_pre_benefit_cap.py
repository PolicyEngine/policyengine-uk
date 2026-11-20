from policyengine_uk.model_api import *


class universal_credit_pre_benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit before benefit cap"
    documentation = (
        "Total entitlement to Universal Credit: the maximum amount less the "
        "income reduction, or nothing for a family that takes Tax-Free "
        "Childcare instead (forgoes_universal_credit_for_tax_free_childcare)."
    )
    definition_period = YEAR
    unit = GBP
    category = BENEFIT
    defined_for = "claims_universal_credit"

    def formula(benunit, period, parameters):
        award = benunit("uc_maximum_amount", period) - benunit(
            "uc_income_reduction", period
        )
        forgoes = benunit("forgoes_universal_credit_for_tax_free_childcare", period)
        return where(forgoes, 0, award)
