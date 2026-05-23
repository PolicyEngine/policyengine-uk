from policyengine_uk.model_api import *


class south_derbyshire_council_tax_reduction_claimant_source_non_dep_exemption(
    Variable
):
    value_type = bool
    entity = Person
    label = (
        "South Derbyshire Council Tax Reduction claimant source non-dependant "
        "deduction exemption"
    )
    documentation = "Source-listed claimant or partner non-dependant deduction exemptions not otherwise represented in PolicyEngine UK, including temporarily suspended disability benefits and Adult Disability Payment."
    definition_period = YEAR
    default_value = False
    reference = "https://www.southderbyshire.gov.uk/assets/attach/15700/South-Derbyshire-CTR-scheme-2026-2027.pdf"
