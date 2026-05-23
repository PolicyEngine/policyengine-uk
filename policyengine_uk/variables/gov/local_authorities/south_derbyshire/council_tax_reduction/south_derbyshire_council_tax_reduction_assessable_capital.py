from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction_assessable_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "South Derbyshire CTR assessable applicant and partner capital"
    documentation = "South Derbyshire tests applicant and partner capital. By default this uses household liquid savings as the available proxy; supply the source-reported applicant/partner amount where child, young-person, or non-dependant capital should be excluded."
    definition_period = YEAR
    unit = GBP
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"

    def formula(benunit, period, parameters):
        source_capital = benunit(
            "south_derbyshire_council_tax_reduction_applicant_partner_capital", period
        )
        return where(
            source_capital >= 0, source_capital, benunit.household("savings", period)
        )
