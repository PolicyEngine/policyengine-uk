from openfisca_uk.model_api import *


class child_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported Child Tax Credit"
    definition_period = YEAR
    unit = "currency-GBP"


class would_claim_ctc(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Child Tax Credit"
    documentation = (
        "Whether this family would claim Child Tax Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        takes_up = (
            random(benunit)
            <= parameters(period).hmrc.tax_credits.child_tax_credit.takeup
        )
        return takes_up | benunit("claims_all_entitled_benefits", period)


class claims_ctc(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this family is imputed to claim Child Tax Credit, based on survey response and take-up rates"
    definition_period = YEAR

    def formula(benunit, period):
        would_claim_CTC = benunit("would_claim_ctc", period)
        claims_legacy_benefits = benunit("claims_legacy_benefits", period)
        return would_claim_CTC & claims_legacy_benefits
