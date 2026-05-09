from policyengine_uk.model_api import *


class ashford_council_tax_reduction_claimant_source_non_dep_exemption(Variable):
    value_type = bool
    entity = Person
    label = "Ashford Council Tax Reduction claimant source non-dependant exemption"
    documentation = "Source input for claimant or partner non-dependant deduction exemptions not otherwise separately exposed in PolicyEngine UK."
    definition_period = YEAR
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )
    default_value = False
