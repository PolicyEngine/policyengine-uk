from openfisca_uk.model_api import *


class pension_credit(Variable):
    label = "Pension Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    reference = "https://www.legislation.gov.uk/ukpga/2002/16/contents"

    def formula(benunit, period, parameters):
        gc = benunit("guarantee_credit", period)
        sc = benunit("savings_credit", period)
        eligible = benunit("is_pension_credit_eligible", period)
        would_claim = benunit("would_claim_pc", period)
        return (eligible & would_claim) * (gc + sc)
