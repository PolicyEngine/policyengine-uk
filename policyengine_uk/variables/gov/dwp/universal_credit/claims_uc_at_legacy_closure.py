from policyengine_uk.model_api import *


class claims_uc_at_legacy_closure(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims Universal Credit when its legacy benefits close"
    documentation = (
        "Whether this family claims Universal Credit because DWP moved it off "
        "its legacy benefits (legacy_benefits_closed), because the "
        "abolition of income-related ESA has reached the claimant's or "
        "partner's award (esa_income_abolition_reached, from 2026-27), or "
        "because the abolition of working-age Housing Benefit has reached its "
        "award (it reports Housing Benefit and housing_benefit_payable_share "
        "is below 1, from 2026-27), and it would claim then "
        "(would_claim_uc_at_legacy_closure). The claim ends "
        "the income-related ESA award (esa_income_report_closed) and the "
        "Housing Benefit award (housing_benefit_eligible), except Housing "
        "Benefit for specified or temporary accommodation (SI 2014/1230 reg "
        "8(3)). A family that does not claim keeps its income-related ESA and "
        "its Housing Benefit for the part of 2026-27 before each abolition "
        "reached it. From 2027-28 neither award is payable, and "
        "legacy_benefits_closed moves a family whose income-related ESA has "
        "ended. Housing Benefit for specified or temporary accommodation "
        "continues."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/44",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/3A",
        "https://www.legislation.gov.uk/nisr/2025/176/article/3A",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
    )

    def formula(benunit, period, parameters):
        # The working-age Housing Benefit abolition (SI 2025/1148 art. 7; NI:
        # SR 2025/176 art. 7) also prompts a claim, from the year it reaches
        # a reported award that no modelled saving keeps. Unlike a migration
        # notice it ends no other award for a family that does not claim,
        # which keeps its Housing Benefit for the part of the year before
        # abolition (housing_benefit_payable_share).
        housing_benefit_abolition_reached = (
            add(benunit, period, ["housing_benefit_reported"]) > 0
        ) & (benunit("housing_benefit_payable_share", period) < 1)
        moved = (
            benunit("legacy_benefits_closed", period)
            | benunit("esa_income_abolition_reached", period)
            | housing_benefit_abolition_reached
        )
        return moved & benunit("would_claim_uc_at_legacy_closure", period)
