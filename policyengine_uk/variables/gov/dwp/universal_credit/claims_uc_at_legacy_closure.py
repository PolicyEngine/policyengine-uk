from policyengine_uk.model_api import *


class claims_uc_at_legacy_closure(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims Universal Credit when its legacy benefits close"
    documentation = (
        "Whether this family claims Universal Credit because DWP moved it off "
        "its legacy benefits (legacy_benefits_closed), or because the "
        "abolition of income-related ESA has reached the claimant's or "
        "partner's award (esa_income_abolition_reached, from 2026-27), and it "
        "would claim then (would_claim_uc_at_legacy_closure). The claim ends "
        "the income-related ESA award (esa_income_report_closed) and the "
        "Housing Benefit award (housing_benefit_eligible). A family that does "
        "not claim keeps its income-related ESA for the part of 2026-27 "
        "before the abolition reached it, and its Housing Benefit, until "
        "legacy_benefits_closed moves it in 2027-28."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/44",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
        "https://www.legislation.gov.uk/nisr/2025/176/article/3A",
    )

    def formula(benunit, period, parameters):
        moved = benunit("legacy_benefits_closed", period) | benunit(
            "esa_income_abolition_reached", period
        )
        return moved & benunit("would_claim_uc_at_legacy_closure", period)
