from policyengine_uk.model_api import *


class north_northamptonshire_council_tax_reduction_claimant_source_non_dep_exemption(
    Variable
):
    value_type = bool
    entity = Person
    label = "Whether a North Northamptonshire CTR claimant or partner has a source-defined non-dependant deduction exemption not otherwise modeled"
    documentation = "Covers source-listed claimant exemptions not otherwise represented in PolicyEngine UK, such as Scottish Adult Disability Living Allowance care component or would-be entitlement to a disability benefit but for suspension, abatement, or hospitalisation."
    definition_period = YEAR
    reference = "https://cms.northnorthants.gov.uk/media/4157/download"
    default_value = False
