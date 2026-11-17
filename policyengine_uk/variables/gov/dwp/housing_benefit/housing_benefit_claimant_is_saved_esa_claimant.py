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
        "entitlement alone does not satisfy art. 7(4)(b). The model otherwise "
        "does not identify the Housing Benefit claimant; neither the benefit "
        "unit head nor its Housing Benefit reporter establishes that identity. "
        "Missing input defaults to false: housing_benefit_payable_share "
        "applies no ESA saving to a couple without this confirmation. It "
        "can infer the identity only for a sole claimant (exactly one "
        "is_claimant_or_partner), whose own positive ESA report has the "
        "appointee saving. In either case a positive claimant/partner ESA "
        "report with esa_income_appointee_saving is required. No dataset "
        "mapping is verified. This is a claimant-specific status, not a "
        "calculation of ESA entitlement."
    )
    reference = (
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
    )
