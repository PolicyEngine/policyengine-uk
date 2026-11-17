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
        "identity to the reports: the saving then applies when every member "
        "who reports Housing Benefit is a claimant or partner with the saved "
        "ESA report (the model takes the Housing Benefit claimant to be one of "
        "those reporters, as has_mixed_age_couple_pension_credit_saving takes "
        "the reporter), or, "
        "when no member reports Housing Benefit, a sole claimant (exactly one "
        "is_claimant_or_partner) has that report. False cannot remove an "
        "identity the reports establish. True overrides the reports: it saves "
        "the award whenever a claimant or partner has the saved ESA report, "
        "even where another member reports Housing Benefit. Supply it only "
        "where the Housing Benefit claimant is known to hold the saved award, "
        "for example a couple whose Housing Benefit and saved ESA reports are "
        "on different members. A saved ESA report counts "
        "only on a claimant or partner, so true cannot save an award whose "
        "saved ESA is reported by a member outside is_claimant_or_partner, "
        "such as the younger member of a couple 20 or more years apart "
        "entered without roles, whom is_claimant_or_partner presumes to be "
        "the claimant's child; supply is_claimant_or_partner for such a "
        "couple. No dataset mapping is "
        "verified. This is a claimant-specific status, not a calculation of "
        "ESA entitlement."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
    )
