from policyengine_uk.model_api import *


class tax_credit_covid_support_payment_extension_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Qualifying historical award for the tax credit support extension"
    definition_period = YEAR
    default_value = False
    documentation = (
        "Externally verified entitlement of the historical tax-credit claim "
        "represented by this benefit unit under the September 2021 extension "
        "Direction. True asserts a final decision, as defined in paragraph 9, "
        "awarding non-nil Working Tax Credit, or nil Working Tax Credit with "
        "non-nil Child Tax Credit, for a period including 2 March 2021. It "
        "also asserts no entitlement to the initial support payment, no "
        "disqualifying pre-2 March termination or non-payability under "
        "paragraph 7, and no knowing fraudulent involvement by the person or "
        "either member of their couple under paragraph 8. A s.16 termination "
        "subsequently cancelled on a s.21A review or reversed on a s.38 "
        "appeal is treated as paragraph 7 specifies. A final decision includes "
        "only the statutory decisions, review outcomes and appeals listed in "
        "paragraph 9. These legal facts are supplied, not inferred from "
        "annual receipts, a later award or current eligibility. Assign the "
        "historical single or joint claim to one benefit unit once, not to "
        "both partners, and keep the fact consistent across payment years. "
        "Historical family changes and recovery of wrongly received payments "
        "are not reconstructed. Initial entitlement takes precedence and "
        "prevents a second extension payment."
    )
    reference = "https://www.gov.uk/government/publications/further-treasury-direction-made-under-section-76-of-the-coronavirus-act-2020/treasury-direction-made-under-section-76-of-the-coronavirus-act-2020"
