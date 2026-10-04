from policyengine_uk.model_api import *


class left_pension_route_at_legacy_closure(Variable):
    value_type = bool
    entity = BenUnit
    label = "Left the pension-age route when its legacy benefits closed"
    documentation = (
        "Whether a family meeting the Pension Credit age conditions left that "
        "route when DWP moved it to Universal Credit (legacy_benefits_closed): "
        "it claimed Universal Credit, or it is a protected mixed-age couple "
        "whose Housing Benefit ended at the notice's deadline, ending the "
        "saving that let it claim Pension Credit or Housing Benefit. A wholly "
        "pension-age family that does not claim Universal Credit stays on the "
        "route and can claim Pension Credit and Housing Benefit afresh."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60A",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.gov.uk/government/publications/housing-benefit-adjudication-circulars-2024/a92024-the-social-security-state-pension-age-claimants-closure-of-tax-credits-amendment-regulations-2024",
    )

    def formula(benunit, period, parameters):
        moved = benunit("legacy_benefits_closed", period) & benunit(
            "meets_pension_credit_age_conditions", period
        )
        return moved & (
            benunit("claims_uc_at_legacy_closure", period)
            | benunit("is_mixed_age_couple", period)
        )
