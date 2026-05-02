from policyengine_uk.model_api import *


class west_northamptonshire_council_tax_reduction_claimant_source_non_dep_exemption(
    Variable
):
    value_type = bool
    entity = Person
    label = "Whether a West Northamptonshire CTR claimant or partner has a source-defined non-dependant deduction exemption not otherwise modeled"
    documentation = "Covers source-listed claimant exemptions not otherwise represented in PolicyEngine UK, such as Pension Age Disability Payment, Adult Disability Payment, Scottish Adult Disability Living Allowance, or would-be entitlement to a disability benefit but for suspension, abatement, or hospitalisation."
    definition_period = YEAR
    reference = "https://cms.westnorthants.gov.uk/media/2065/download"
    default_value = False
