from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_sdp_transitional_award(Variable):
    value_type = bool
    entity = BenUnit
    label = "Bassetlaw Council Tax Reduction SDP transitional award flag"
    documentation = "Source input for Universal Credit transitional protection that compensates for the loss of Severe Disability Premium under Bassetlaw Class G."
    definition_period = YEAR
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"
    default_value = False
