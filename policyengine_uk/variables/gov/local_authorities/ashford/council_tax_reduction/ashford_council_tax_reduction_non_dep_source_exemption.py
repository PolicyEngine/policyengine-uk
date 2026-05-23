from policyengine_uk.model_api import *


class ashford_council_tax_reduction_non_dep_source_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Ashford Council Tax Reduction source non-dependant exemption"
    documentation = "Source input for non-dependant exemptions not otherwise separately exposed in PolicyEngine UK, such as normal home elsewhere, training allowance, long-term hospital patients, or armed-forces operational absence."
    definition_period = YEAR
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )
    default_value = False
