from policyengine_uk.model_api import *


class st_helens_council_tax_reduction_uc_regulation_60a_pensioner(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether St Helens' Universal Credit regulation 60A pensioner exception applies"
    )
    documentation = "Footnote 1 keeps pension-age Universal Credit recipients on the prescribed pensioner scheme where their Universal Credit award arises from the closure of Working Tax Credit (regulation 60A of the Universal Credit (Transitional Provisions) Regulations 2014)."
    definition_period = YEAR
    reference = "https://www.sthelens.gov.uk/media/13997/St-Helens-CTR-scheme-2026/pdf/St_Helens_CTR_scheme_2026.pdf"
    default_value = False
