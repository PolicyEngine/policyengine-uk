from openfisca_uk.model_api import *


class claims_HB(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Housing Benefit"
    documentation = (
        "Whether this family would claim Housing Benefit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        would_claim_HB = benunit("would_claim_HB", period)
        claims_legacy_benefits = benunit("claims_legacy_benefits", period)
        return would_claim_HB & claims_legacy_benefits