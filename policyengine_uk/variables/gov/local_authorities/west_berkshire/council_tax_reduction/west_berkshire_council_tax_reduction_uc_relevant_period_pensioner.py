from policyengine_uk.model_api import *


class west_berkshire_council_tax_reduction_uc_relevant_period_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether West Berkshire disregards a pension-age Universal Credit award during the relevant period"
    documentation = "West Berkshire paragraph 3(2) disregards a Universal Credit award for pensioner-status routing during the relevant period. When set, a pension-age UC claimant remains in the prescribed pensioner CTR scheme rather than West Berkshire's local working-age scheme. Default False."
    definition_period = YEAR
    reference = "https://www.westberks.gov.uk/media/66425/Council-Tax-Reduction-Scheme-2026-27/pdf/The_Council_Tax_Reduction_Scheme_as_amended_by_West_Berkshire_Council_2026.pdf"
    default_value = False
