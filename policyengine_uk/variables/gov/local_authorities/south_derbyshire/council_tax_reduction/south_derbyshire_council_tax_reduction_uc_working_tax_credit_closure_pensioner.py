from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction_uc_working_tax_credit_closure_pensioner(
    Variable
):
    value_type = bool
    entity = BenUnit
    label = (
        "Whether a South Derbyshire pension-age UC claimant remains under the "
        "pensioner scheme because UC follows Working Tax Credit closure"
    )
    definition_period = YEAR
    default_value = False
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"
