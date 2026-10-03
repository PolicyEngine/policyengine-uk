from policyengine_uk.model_api import *


class claims_uc_at_legacy_closure(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims Universal Credit when its legacy benefits close"
    documentation = (
        "Whether this family claims Universal Credit because DWP moved it off "
        "its legacy benefits (legacy_benefits_closed) or its working-age "
        "Housing Benefit award was abolished, and it would claim then "
        "(would_claim_uc_at_legacy_closure)."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/44",
        "https://www.legislation.gov.uk/uksi/2025/1148/article/7",
        "https://www.legislation.gov.uk/nisr/2025/176/article/7",
    )

    def formula(benunit, period, parameters):
        # The working-age Housing Benefit abolition (SI 2025/1148 art. 7; NI:
        # SR 2025/176 art. 7) also prompts a claim. Unlike a migration notice
        # it ends no other award for a family that does not claim, which keeps
        # its Housing Benefit for the part of the year before abolition
        # (housing_benefit_payable_share).
        housing_benefit_abolished = (
            add(benunit, period, ["housing_benefit_reported"]) > 0
        ) & (benunit("housing_benefit_payable_share", period) < 1)
        closed = benunit("legacy_benefits_closed", period) | housing_benefit_abolished
        return closed & benunit("would_claim_uc_at_legacy_closure", period)
