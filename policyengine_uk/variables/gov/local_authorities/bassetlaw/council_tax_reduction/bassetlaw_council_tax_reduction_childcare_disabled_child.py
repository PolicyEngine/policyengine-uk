from policyengine_uk.model_api import *


class bassetlaw_council_tax_reduction_childcare_disabled_child(Variable):
    value_type = bool
    entity = Person
    label = "Bassetlaw Council Tax Reduction source childcare disabled child flag"
    definition_period = YEAR
    reference = "https://www.bassetlaw.gov.uk/media/15ehht0s/council-tax-reduction-scheme-working-age-2026-2027.pdf"
    default_value = False
