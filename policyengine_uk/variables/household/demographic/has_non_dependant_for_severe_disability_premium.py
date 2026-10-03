from policyengine_uk.model_api import *


class has_non_dependant_for_severe_disability_premium(Variable):
    value_type = bool
    entity = BenUnit
    label = "Has a non-dependant who blocks the severe disability premium"
    documentation = (
        "A non-dependant aged 18 or over normally resides with the claimant, "
        "which bars the legacy severe disability premium. Non-dependants who "
        "receive a severe disability premium qualifying benefit, or who are "
        "blind, are ignored. Every household member aged 18 or over is "
        "treated as a non-dependant unless they are in the claimant's family: "
        "the claimant, their partner, and children and qualifying young "
        "persons (the Child Benefit definition that the Regulations' "
        "'young person' uses). A 19-year-old is a young person only if their "
        "course started, or they enrolled or were accepted, before 19 "
        "(age_started_or_accepted_current_education_or_training; unknown "
        "counts as not met). The Regulations' exclusion of young people who "
        "claim benefits themselves (HB Regs reg 19(2), IS Regs reg 14(2)) is "
        "approximated by receives_benefits_in_own_right. Their exclusion of "
        "a young person to whom section 6 of the Children (Leaving Care) Act "
        "2000 applies (HB Regs reg 19(2)(c), IS Regs reg 14(2)(c)) is not "
        "modelled. The people in section 6(2)(a) to (bb) are children aged 16 "
        "or 17, below the non-dependant age, so for them the omission cannot "
        "change the premium; the people prescribed under section 6(4) "
        "(looked after in Scotland) are also under 18 (S.I. 2004/747 reg "
        "2(2)(a)). The care-leaver bursary and current local-authority care "
        "inputs do not identify the historical care status needed for "
        "section 6. The model cannot "
        "identify the other people the "
        "Regulations exclude from the definition (for example joint "
        "occupiers, commercial lodgers or landlords, and carers engaged by a "
        "charity), apply the 12-week rule for someone who moves in to care "
        "(IS, ESA and JSA only), or treat someone as blind for 28 weeks after "
        "regaining their sight."
    )
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/3",
        "https://www.legislation.gov.uk/uksi/2006/213/regulation/19",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/14",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/3",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/14",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/2/paragraph/13",
        "https://www.legislation.gov.uk/ukpga/2000/35/section/6",
        "https://www.legislation.gov.uk/uksi/2004/747/regulation/2",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.disability_premia
        person = benunit.members
        counted = (
            (person("age", period) >= p.severe_non_dependant_age)
            & ~person("receives_severe_disability_premium_qualifying_benefit", period)
            & ~person("is_blind", period)
        )
        # The claimant's family is never a non-dependant (HB Regs reg 3(2)(a);
        # "young person" is a Child Benefit qualifying young person, reg 19).
        family = person("is_claimant_or_partner", period) | person(
            "is_child_or_qualifying_young_person_for_child_benefit", period
        )
        # Counted residents of the household, less the claimant's family.
        in_household = benunit.max(person.household.sum(counted))
        return in_household > benunit.sum(counted & family)
