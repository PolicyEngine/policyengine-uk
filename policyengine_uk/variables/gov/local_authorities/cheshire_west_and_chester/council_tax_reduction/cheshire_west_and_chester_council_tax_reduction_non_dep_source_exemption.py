from policyengine_uk.model_api import *


class cheshire_west_and_chester_council_tax_reduction_non_dep_source_exemption(
    Variable
):
    value_type = bool
    entity = Person
    label = "Whether a Cheshire West and Chester CTR non-dependant has a source-listed deduction exemption not otherwise modeled"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK, such as normal home elsewhere, youth training, long-term patient status, armed forces away, or a council tax discount-disregard status."
    definition_period = YEAR
    reference = "https://www.cheshirewestandchester.gov.uk/asset-library/council-tax-reduction-summary-2026-2027-annex-a-part-2.pdf"
    default_value = False
