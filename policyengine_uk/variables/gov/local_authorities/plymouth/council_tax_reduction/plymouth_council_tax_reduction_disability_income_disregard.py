from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_disability_income_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Plymouth Council Tax Support annual disability premium income disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        modeled_premia = (
            benunit("disability_premium", period)
            + benunit("enhanced_disability_premium", period)
            + benunit("severe_disability_premium", period)
        )
        source_amount = benunit(
            "plymouth_council_tax_reduction_source_disability_income_disregard",
            period,
        )
        return modeled_premia + source_amount
