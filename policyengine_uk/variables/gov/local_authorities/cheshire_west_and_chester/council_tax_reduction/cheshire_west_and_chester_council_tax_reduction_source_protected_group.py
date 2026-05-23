from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_source_protected_group(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether the Cheshire West and Chester CTR claimant is in a source-listed protected class not otherwise modeled"
    documentation = "Covers source-listed protected Class C or D triggers not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-2.pdf"
    default_value = False
