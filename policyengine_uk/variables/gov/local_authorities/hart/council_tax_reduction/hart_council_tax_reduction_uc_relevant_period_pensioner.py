from policyengine_uk.model_api import *


class hart_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether Hart's Universal Credit relevant-period pensioner exception applies"
    )
    definition_period = YEAR
    reference = "https://www.hart.gov.uk/sites/default/files/2026-04/Council-Tax-Reduction-Scheme-2026-27.pdf"
    default_value = False
