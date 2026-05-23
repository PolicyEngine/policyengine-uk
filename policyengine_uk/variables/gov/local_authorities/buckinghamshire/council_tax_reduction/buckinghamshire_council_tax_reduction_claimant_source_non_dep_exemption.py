from policyengine_uk.model_api import *


class buckinghamshire_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Whether a Buckinghamshire CTR claimant or partner has a source-defined non-dependant deduction exemption not otherwise modeled"
    documentation = "Covers source-listed claimant exemptions not otherwise represented in PolicyEngine UK, such as would-be entitlement to a disability benefit but for suspension, abatement, or hospitalisation."
    definition_period = YEAR
    reference = "https://buckinghamshire.moderngov.co.uk/documents/s115727/Appendix%204%20Council%20Tax%20Reduction%20Scheme%20Policy.pdf"
    default_value = False
