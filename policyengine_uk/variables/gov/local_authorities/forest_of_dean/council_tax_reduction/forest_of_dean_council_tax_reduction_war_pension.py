from policyengine_uk.model_api import *


class forest_of_dean_council_tax_reduction_war_pension(Variable):
    value_type = bool
    entity = BenUnit
    label = (
        "Forest of Dean Class B claimant or partner receives a war pension or war"
        " widow's pension"
    )
    documentation = "Class B (h) qualifies for protected support where the claimant or partner receives a War Pension or War Widow's Pension. PolicyEngine UK does not model those payments directly, so this Forest of Dean-scoped source input flags the case."
    definition_period = YEAR
    reference = "https://www.fdean.gov.uk/media/r4ff2lok/council-tax-support-scheme-for-working-age-customers-2026-to-2027.pdf"
    default_value = False
