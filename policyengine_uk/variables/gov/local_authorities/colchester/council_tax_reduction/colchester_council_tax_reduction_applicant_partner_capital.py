from policyengine_uk.model_api import *


class colchester_council_tax_reduction_applicant_partner_capital(Variable):
    value_type = float
    entity = BenUnit
    label = "Colchester CTR applicant and partner source-reported capital"
    documentation = "Use this input when a household contains non-dependants, because Colchester assesses applicant and partner capital rather than household-wide savings."
    definition_period = YEAR
    unit = GBP
    reference = "https://cbccrmdata.blob.core.windows.net/noteattachment/CBC-null-Local-council-tax-support-policy-updated-01-04-26-Local%20Council%20Tax%20support%20policy.pdf"
    default_value = 0
