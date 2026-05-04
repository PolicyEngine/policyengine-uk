from policyengine_uk.model_api import *


class colchester_council_tax_reduction_childcare_disabled_child(Variable):
    value_type = bool
    entity = Person
    label = "Colchester CTR source-listed disabled child for childcare"
    documentation = "Covers source disabled-child status for childcare age-limit rules not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://cbccrmdata.blob.core.windows.net/noteattachment/CBC-null-Local-council-tax-support-policy-updated-01-04-26-Local%20Council%20Tax%20support%20policy.pdf"
    default_value = False
