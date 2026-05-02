from policyengine_uk.model_api import *


class basildon_council_tax_reduction_working_tax_credit_disability_element(Variable):
    value_type = bool
    entity = BenUnit
    label = "Basildon CTR Working Tax Credit disability element protected-group trigger"
    definition_period = YEAR
    reference = "https://www.basildon.gov.uk/media/11563/Basildon-Council-Council-Tax-Reduction-Scheme-2026-27/pdf/Basildon_S13A_202627_Final.pdf?m=1771316212763"
    default_value = False
