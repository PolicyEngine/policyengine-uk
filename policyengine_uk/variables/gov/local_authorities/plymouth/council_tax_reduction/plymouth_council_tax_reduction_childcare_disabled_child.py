from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_childcare_disabled_child(Variable):
    value_type = bool
    entity = Person
    label = "Plymouth Council Tax Support source-defined disabled child for childcare deduction"
    documentation = "Covers source disabled-child status for childcare age-limit rules not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = False
