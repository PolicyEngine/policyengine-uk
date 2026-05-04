from policyengine_uk.model_api import *


class colchester_council_tax_reduction_source_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Colchester CTR source-listed protected-group status not otherwise represented"
    )
    definition_period = YEAR
    reference = "https://cbccrmdata.blob.core.windows.net/noteattachment/CBC-null-Local-council-tax-support-policy-updated-01-04-26-Local%20Council%20Tax%20support%20policy.pdf"
    default_value = False
