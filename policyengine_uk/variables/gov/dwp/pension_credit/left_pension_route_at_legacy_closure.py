from policyengine_uk.model_api import *


class left_pension_route_at_legacy_closure(Variable):
    value_type = bool
    entity = BenUnit
    label = "Left the pension-age route when its legacy benefits closed"
    documentation = (
        "Whether a family meeting the Pension Credit age conditions left that "
        "route when DWP moved it to Universal Credit (legacy_benefits_closed): "
        "it claimed Universal Credit at the closure and is eligible for it. A "
        "family that does not claim keeps the route. A wholly pension-age one "
        "can claim Pension Credit and Housing Benefit afresh, and a protected "
        "mixed-age couple can reclaim Housing Benefit within three months, "
        "keeping its saving. A claimant refused Universal Credit, say on "
        "capital, is taken to stay on the route: the transitional capital "
        "disregard that would admit a tax credit migrant is not modelled."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/46",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/51",
        "https://www.legislation.gov.uk/uksi/2014/1230/regulation/60A",
        "https://www.legislation.gov.uk/uksi/2019/37/article/4",
        "https://www.gov.uk/government/publications/housing-benefit-adjudication-circulars-2024/a92024-the-social-security-state-pension-age-claimants-closure-of-tax-credits-amendment-regulations-2024",
    )

    def formula(benunit, period, parameters):
        moved = benunit("legacy_benefits_closed", period) & benunit(
            "meets_pension_credit_age_conditions", period
        )
        # SI 2019/37 art. 4(3)(b)(ii), inserted by SI 2024/604, lets a
        # protected couple that did not claim Universal Credit reclaim Housing
        # Benefit within three months of its award ending and keep the saving
        # (DWP HB circular A9/2024 paras 12-13), so only a claim moves it.
        return (
            moved
            & benunit("claims_uc_at_legacy_closure", period)
            & benunit("is_uc_eligible", period)
        )
