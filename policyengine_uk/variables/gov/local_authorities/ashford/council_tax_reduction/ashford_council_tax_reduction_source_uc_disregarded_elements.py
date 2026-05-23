from policyengine_uk.model_api import *


class ashford_council_tax_reduction_source_uc_disregarded_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Ashford Council Tax Reduction source-disregarded Universal Credit elements"
    documentation = "Source input for UC elements disregarded by Ashford's scheme that are not separately exposed in PolicyEngine UK, such as transitional protection."
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.ashford.gov.uk/media/0n4nud13/ashford-ctr-scheme-2026-final.pdf"
    )
    default_value = 0
