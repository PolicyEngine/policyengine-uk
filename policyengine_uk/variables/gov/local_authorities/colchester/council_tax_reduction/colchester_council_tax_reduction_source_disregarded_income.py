from policyengine_uk.model_api import *


class colchester_council_tax_reduction_source_disregarded_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Colchester CTR source-listed disregarded income not otherwise represented"
    definition_period = YEAR
    unit = GBP
    reference = "https://cbccrmdata.blob.core.windows.net/noteattachment/CBC-null-Local-council-tax-support-policy-updated-01-04-26-Local%20Council%20Tax%20support%20policy.pdf"
    default_value = 0
