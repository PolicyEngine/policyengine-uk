from policyengine_uk.model_api import *


class council_tax_reduction_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction disability and carer premiums"
    documentation = (
        "The disability and carer premiums in the Council Tax Reduction "
        "applicable amount, which are the applicant's. A pensioner "
        "(council_tax_reduction_pensioner) has the pension-age schedule (the "
        "severe disability and carer premiums), anyone else the working-age "
        "schedule. Where the applicant is the benefit unit's claimant, these "
        "are the benefit unit's premiums (pension_age_benefits_premiums or "
        "working_age_benefits_premiums). Where the household head applies "
        "alone (council_tax_reduction_head_applies_alone), they are the "
        "premiums of a single claimant on the head's own circumstances, under "
        "the same conditions: the disability and enhanced disability premiums "
        "on her own disability (working age only); the severe disability "
        "premium if she receives a qualifying benefit, no carer benefit is "
        "paid for caring for her, and no other resident aged 18 or over is "
        "her non-dependant (everyone else in the household, since she has no "
        "partner or children, unless they receive a qualifying benefit or are "
        "blind); and the carer premium if she is entitled to a carer benefit. "
        "Whom a carer benefit is paid for caring for comes from "
        "is_cared_for_by_carer_benefit_recipient, which gives a carer in her "
        "own benefit unit to her but a carer in another benefit unit only to "
        "that unit's claimants and partners. So a carer outside her benefit "
        "unit (who must then be blind or on a qualifying benefit, or they "
        "would bar the premium as her non-dependant) does not end her severe "
        "disability premium, though in law they would."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/1/paragraph/6",
        "https://www.legislation.gov.uk/uksi/2012/2885/schedule/2",
        "https://www.legislation.gov.uk/ssi/2012/319/regulation/20",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/1/paragraph/1",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
    )

    def formula(benunit, period, parameters):
        pensioner = benunit("council_tax_reduction_pensioner", period)
        # The working-age severe disability premium takes Council Tax
        # Reduction's own family test (council_tax_reduction_severe_disability_
        # premium, which differs from the shared premium in Scotland).
        benefit_unit_premiums = where(
            pensioner,
            benunit("pension_age_benefits_premiums", period),
            benunit("working_age_benefits_premiums", period)
            + (
                benunit("council_tax_reduction_severe_disability_premium", period)
                - benunit("severe_disability_premium", period)
            ),
        )
        head_applies_alone = benunit("council_tax_reduction_head_applies_alone", period)
        person = benunit.members
        head = person(
            "is_council_tax_reduction_applicant_or_partner", period
        ) & benunit.project(head_applies_alone)

        def head_has(condition):
            return benunit.any(head & condition)

        disability = parameters(period).gov.dwp.disability_premia
        carer = parameters(period).gov.dwp.carer_premium
        # The severe disability premium's non-dependants: every resident aged
        # 18 or over outside the applicant's family who neither receives a
        # qualifying benefit nor is blind (has_non_dependant_for_severe_
        # disability_premium). The head's family is the head alone.
        counted = (
            (person("age", period) >= disability.severe_non_dependant_age)
            & ~person("receives_severe_disability_premium_qualifying_benefit", period)
            & ~person("is_blind", period)
        )
        others_counted = benunit.max(person.household.sum(counted)) - benunit.sum(
            counted & head
        )
        severe = (
            head_has(
                person("receives_severe_disability_premium_qualifying_benefit", period)
                & ~person("is_cared_for_by_carer_benefit_recipient", period)
            )
            & (others_counted == 0)
        ) * disability.severe_single
        carer_premium = (
            head_has(person("is_entitled_to_carer_benefit", period)) * carer.single
        )
        # The pension-age schedules have no adult disability or enhanced
        # disability premium.
        disability_premiums = ~pensioner * (
            head_has(person("is_disabled_for_benefits", period))
            * disability.disability_single
            + head_has(person("is_enhanced_disabled_for_benefits", period))
            * disability.enhanced_single
        )
        head_premiums = (disability_premiums + severe + carer_premium) * WEEKS_IN_YEAR
        return where(head_applies_alone, head_premiums, benefit_unit_premiums)
