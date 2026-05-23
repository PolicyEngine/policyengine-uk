from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_disability_or_esa_component(Variable):
    value_type = bool
    entity = BenUnit
    label = "Plymouth Council Tax Support disability or ESA component earnings disregard applies"
    definition_period = YEAR
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        disability_premia = benunit("disability_premium", period) + benunit(
            "severe_disability_premium", period
        )
        esa_component = benunit(
            "plymouth_council_tax_reduction_esa_support_component", period
        )
        source_trigger = benunit(
            "plymouth_council_tax_reduction_source_disability_or_esa_component",
            period,
        )
        return (disability_premia > 0) | (esa_component > 0) | source_trigger
