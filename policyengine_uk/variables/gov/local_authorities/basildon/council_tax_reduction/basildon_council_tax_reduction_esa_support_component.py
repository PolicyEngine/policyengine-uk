from policyengine_uk.model_api import *


class basildon_council_tax_reduction_esa_support_component(Variable):
    value_type = float
    entity = BenUnit
    label = "Basildon CTR annual ESA support component amount"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.basildon.gov.uk/media/11563/Basildon-Council-Council-Tax-Reduction-Scheme-2026-27/pdf/Basildon_S13A_202627_Final.pdf?m=1771316212763"
    default_value = 0
