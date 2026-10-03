from policyengine_uk.model_api import *


class council_tax_reduction_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction disability and carer premiums"
    documentation = (
        "The disability and carer premiums in the Council Tax Reduction "
        "applicable amount, which are the applicant's. Where the applicant is "
        "the benefit unit's claimant, these are the benefit unit's premiums "
        "(benefits_premiums). Where the household head applies alone "
        "(council_tax_reduction_head_applies_alone), they are the premiums a "
        "single claimant would get on the head's own circumstances: the "
        "single rates of the disability, enhanced disability, severe "
        "disability and carer premiums, each on the same person-level "
        "condition benefits_premiums uses."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/20",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/1",
    )

    def formula(benunit, period, parameters):
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        person = benunit.members
        head = person(
            "is_council_tax_reduction_applicant_or_partner", period
        ) & benunit.project(head_applies_alone)

        def head_qualifies(condition):
            return benunit.any(head & person(condition, period))

        disability = parameters(period).gov.dwp.disability_premia
        carer = parameters(period).gov.dwp.carer_premium
        weekly_single_premiums = (
            head_qualifies("is_disabled_for_benefits") * disability.disability_single
            + head_qualifies("is_enhanced_disabled_for_benefits")
            * disability.enhanced_single
            + head_qualifies("is_severely_disabled_for_benefits")
            * disability.severe_single
            + head_qualifies("is_carer_for_benefits") * carer.single
        )
        return where(
            head_applies_alone,
            weekly_single_premiums * WEEKS_IN_YEAR,
            benunit("benefits_premiums", period),
        )
