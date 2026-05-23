from policyengine_uk.model_api import *


class would_claim_council_tax_reduction(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Council Tax Reduction"
    documentation = (
        "Whether this benefit unit would claim Council Tax Reduction if eligible."
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        claims_all_entitled_benefits = benunit("claims_all_entitled_benefits", period)
        reported_ctr = benunit("council_tax_benefit_reported", period) > 0
        return claims_all_entitled_benefits | reported_ctr
