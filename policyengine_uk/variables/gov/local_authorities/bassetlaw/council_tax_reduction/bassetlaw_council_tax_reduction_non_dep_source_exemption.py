from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Bassetlaw Council Tax Reduction source non-dependant exemption"
    documentation = "Source input for non-dependant exemptions not otherwise separately exposed in PolicyEngine UK, such as normal home elsewhere, training allowance, long-term hospital patients, or armed-forces operational absence."
    definition_period = YEAR
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"
    default_value = False
