from policyengine_uk.model_api import *


class council_tax_reduction_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = "Council Tax Reduction disability and carer premiums"
    documentation = (
        "The disability and carer premiums in the Council Tax Reduction "
        "applicable amount. A pensioner (council_tax_reduction_pensioner) has "
        "the pension-age schedule (the severe disability and carer premiums, "
        "and the disabled child and enhanced disability premiums for each "
        "qualifying child or young person in the family), anyone else the "
        "working-age schedule. Where the applicant is the benefit unit's "
        "claimant, these are the benefit unit's premiums: for a pensioner, "
        "pension_age_benefits_premiums plus "
        "council_tax_reduction_pensioner_child_disability_premiums; otherwise "
        "working_age_benefits_premiums, with Council Tax Reduction's own "
        "severe disability and enhanced disability premiums in place of the "
        "shared ones. Where the household head applies "
        "alone (council_tax_reduction_head_applies_alone), they are the "
        "premiums of a single claimant on the head's own circumstances, under "
        "the same conditions: the disability premium on her own disability and "
        "the enhanced disability premium on the scheme's condition "
        "(meets_council_tax_reduction_enhanced_disability_premium_condition), "
        "both working age only; the severe disability "
        "premium if she receives a qualifying benefit, no carer benefit is "
        "paid for caring for her, and no other resident aged 18 or over is "
        "her non-dependant (everyone else in the household, since she has no "
        "partner or children, unless they receive a qualifying benefit or are "
        "blind); and the carer premium if she is entitled to a carer benefit. "
        "At working age the benefit unit's carer premium comes from "
        "council_tax_reduction_carer_premium, which in Scotland also counts "
        "an award of Universal Credit which includes the carer element. "
        "Whom a carer benefit is paid for caring for comes from "
        "is_cared_for_by_carer_benefit_recipient, which gives a carer in her "
        "own benefit unit to her but a carer in another benefit unit only to "
        "that unit's claimants and partners. So a carer outside her benefit "
        "unit does not end her severe disability premium, though in law they "
        "would. Such a carer is under 18, blind or on a qualifying benefit, "
        "since any other resident aged 18 or over already bars the premium as "
        "her non-dependant."
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
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/1/paragraph/6",
    )

    def formula(benunit, period, parameters):
        pensioner = benunit("council_tax_reduction_pensioner", period)
        # The working-age severe disability premium takes Council Tax
        # Reduction's own family test (council_tax_reduction_severe_disability_
        # premium), and the working-age carer premium its own caring test
        # (council_tax_reduction_carer_premium); both differ from the shared
        # premiums only in Scotland. The enhanced disability premium takes the
        # scheme's own condition (council_tax_reduction_enhanced_disability_
        # premium).
        benefit_unit_premiums = where(
            pensioner,
            # A pensioner's premiums include the disabled child and enhanced
            # disability premiums for the family's children and young persons
            # (SI 2012/2885 Sch 1 para 6(1)(d); WSI 2013/3029 Sch 1 para
            # 1(1)(d); SSI 2012/319 reg 20(d)).
            benunit("pension_age_benefits_premiums", period)
            + benunit(
                "council_tax_reduction_pensioner_child_disability_premiums", period
            ),
            benunit("working_age_benefits_premiums", period)
            + (
                benunit("council_tax_reduction_severe_disability_premium", period)
                - benunit("severe_disability_premium", period)
            )
            + (
                benunit("council_tax_reduction_enhanced_disability_premium", period)
                - benunit("enhanced_disability_premium", period)
            )
            + (
                benunit("council_tax_reduction_carer_premium", period)
                - benunit("carer_premium", period)
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
        # A head who applies alone holds no Universal Credit award of her own
        # (the benefit unit's claimant and partner hold its award), so
        # Scotland's carer element limb (council_tax_reduction_carer_premium)
        # never reaches her.
        carer_premium = (
            head_has(person("is_entitled_to_carer_benefit", period)) * carer.single
        )
        # The pension-age schedules have no adult disability or enhanced
        # disability premium.
        disability_premiums = ~pensioner * (
            head_has(person("is_disabled_for_benefits", period))
            * disability.disability_single
            + head_has(
                person(
                    "meets_council_tax_reduction_enhanced_disability_premium_condition",
                    period,
                )
            )
            * disability.enhanced_single
        )
        head_premiums = (disability_premiums + severe + carer_premium) * WEEKS_IN_YEAR
        return where(head_applies_alone, head_premiums, benefit_unit_premiums)
