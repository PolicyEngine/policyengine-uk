from policyengine_uk.model_api import *


class babergh_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Babergh CTR claimant source-defined non-dependant deduction exemption"
    documentation = "Covers source-listed claimant or partner non-dependant deduction exemptions not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    default_value = False
    reference = (
        "https://www.babergh.gov.uk/documents/d/babergh/bdc-ctr-scheme-2026_27-v4-pdf"
    )
