from policyengine_uk.model_api import *


class housing_benefit_claimant_is_saved_esa_claimant(Variable):
    value_type = bool
    entity = BenUnit
    label = "Housing Benefit claimant is the saved income-related ESA claimant"
    definition_period = YEAR
    default_value = False
    documentation = (
        "Supplied confirmation that the Housing Benefit claimant personally "
        "holds the income-related ESA award protected by the art. 3A(2) "
        "appointee saving immediately before abolition (1 July 2026 in "
        "Great Britain; 1 October 2026 in Northern Ireland). A partner's "
        "entitlement alone does not satisfy art. 7(4)(b). True confirms the "
        "identity: housing_benefit_payable_share then saves the award when a "
        "claimant or partner has a positive ESA report with "
        "esa_income_appointee_saving. False, the default, leaves the "
        "identity to the reports. The model uses the Housing Benefit "
        "reporter as the Housing Benefit claimant, as "
        "has_mixed_age_couple_pension_credit_saving does, so the saving "
        "applies when exactly one member reports Housing Benefit and that "
        "member is a claimant or partner with the saved ESA report, or, when "
        "no member reports Housing Benefit, a sole claimant (exactly one "
        "is_claimant_or_partner) has that report. False cannot remove an "
        "identity the reports establish. Supply true where the reports do "
        "not show it, for example a couple whose Housing Benefit and saved "
        "ESA reports are on different members. No dataset mapping is "
        "verified. This is a claimant-specific status, not a calculation of "
        "ESA entitlement."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
    )
