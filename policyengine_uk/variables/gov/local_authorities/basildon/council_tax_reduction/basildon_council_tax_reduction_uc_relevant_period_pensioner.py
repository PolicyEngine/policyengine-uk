from policyengine_uk.model_api import *


class basildon_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether a Basildon pension-age Universal Credit award remains in the prescribed pensioner CTR scheme during the source relevant period"
    documentation = "Covers the source transitional protection where a Universal Credit award is disregarded for pensioner-status classification."
    definition_period = YEAR
    reference = "https://www.basildon.gov.uk/media/11563/Basildon-Council-Council-Tax-Reduction-Scheme-2026-27/pdf/Basildon_S13A_202627_Final.pdf?m=1771316212763"
    default_value = False
