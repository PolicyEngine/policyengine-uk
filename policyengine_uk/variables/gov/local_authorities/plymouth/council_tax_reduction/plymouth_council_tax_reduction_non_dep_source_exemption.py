from policyengine_uk.model_api import *


class plymouth_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Plymouth Council Tax Support non-dependant source exemption"
    documentation = "Covers source-listed non-dependant deduction exemptions not otherwise represented in PolicyEngine UK, including long-term patients, armed forces away on operations, youth training allowances, and Council Tax discount-disregarded status."
    definition_period = YEAR
    reference = "https://www.plymouth.gov.uk/sites/default/files/2026-03/Plymouth-CTR-Scheme-2026-2027.pdf"
    default_value = False
