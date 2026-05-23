from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = (
        "South Derbyshire Council Tax Reduction non-dependant source deduction "
        "exemption"
    )
    documentation = "Source-listed non-dependant deduction exemptions not otherwise represented in PolicyEngine UK, such as normally living elsewhere, youth training allowance, long hospital stays, armed forces operations, and Thalidomide payments."
    definition_period = YEAR
    default_value = False
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"
