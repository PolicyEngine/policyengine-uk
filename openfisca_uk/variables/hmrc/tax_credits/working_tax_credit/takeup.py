from openfisca_uk.model_api import *


class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Reported Working Tax Credit"
    definition_period = YEAR
    unit = "currency-GBP"


class would_claim_wtc(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Working Tax Credit"
    documentation = (
        "Whether this family would claim Working Tax Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        takeup_rate = parameters(
            period
        ).hmrc.tax_credits.working_tax_credit.takeup
        takes_up = random(benunit) < takeup_rate
        would_take_up = benunit("claims_legacy_benefits", period) & takes_up
        return would_take_up | benunit("claims_all_entitled_benefits", period)


class claims_wtc(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this family is imputed to claim Working Tax Credit, based on survey response and take-up rates"
    definition_period = YEAR

    def formula(benunit, period):
        would_claim_wtc = benunit("would_claim_wtc", period)
        claims_legacy_benefits = benunit("claims_legacy_benefits", period)
        return would_claim_wtc & claims_legacy_benefits
