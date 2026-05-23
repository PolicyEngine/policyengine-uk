from policyengine_uk.model_api import *


class cotswold_council_tax_reduction_childcare_disabled_partner(Variable):
    value_type = bool
    entity = Person
    label = "Cotswold Council Tax Support source childcare disabled partner flag"
    definition_period = YEAR
    reference = "https://cotswold.gov.uk/media/k04l1hc2/cdc-cts-scheme-2026-27.pdf"
    default_value = False
