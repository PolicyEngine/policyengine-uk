from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Bassetlaw Council Tax Reduction claimant source non-dependant exemption"
    documentation = "Source input for claimant or partner non-dependant deduction exemptions not otherwise separately exposed in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"
    default_value = False
