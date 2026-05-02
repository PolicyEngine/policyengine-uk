from policyengine_uk.model_api import *


class mid_suffolk_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Mid Suffolk CTR source-defined non-dependant exemption"
    documentation = "Covers source-listed non-dependant exemptions not otherwise represented in PolicyEngine UK."
    definition_period = YEAR
    default_value = False
    reference = "https://www.midsuffolk.gov.uk/documents/d/asset-library-54706/msdc-ctr-scheme-2026_27-v4-pdf"
