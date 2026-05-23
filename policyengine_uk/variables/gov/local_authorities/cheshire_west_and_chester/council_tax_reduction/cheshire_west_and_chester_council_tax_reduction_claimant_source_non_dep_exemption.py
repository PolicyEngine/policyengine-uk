from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_claimant_source_non_dep_exemption(
    Variable
):
    value_type = bool
    entity = Person
    label = "Whether a Cheshire West and Chester CTR claimant has a source-listed non-dependant deduction exemption not otherwise modeled"
    documentation = "Covers source-listed claimant exemptions not otherwise represented in PolicyEngine UK, such as suspended entitlement to disability benefits or devolved disability payments."
    definition_period = YEAR
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-2.pdf"
    default_value = False
