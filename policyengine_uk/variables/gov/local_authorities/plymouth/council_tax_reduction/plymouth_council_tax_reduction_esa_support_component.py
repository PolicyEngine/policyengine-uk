from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_esa_support_component(Variable):
    value_type = float
    entity = BenUnit
    label = "Plymouth Council Tax Support annual ESA support or work-related activity component amount to disregard"
    definition_period = YEAR
    unit = GBP
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = 0
