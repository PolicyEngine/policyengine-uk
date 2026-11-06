"""Who the working-age council tax reduction assessment covers.

The applicant is the person liable for the council tax, and the means test
covers the applicant and their partner (SSI 2021/249 reg 36; WSI 2013/3029
Sch 6 para 7): is_council_tax_reduction_applicant_or_partner. Where the
household head is liable but is not the benefit unit's claimant or partner
(council_tax_reduction_head_applies_alone), the head applies as a single
person with no partner or children, and the benefit unit's awards (Universal
Credit, Income Support, income-based JSA, income-related ESA, tax credits)
and children are its claimant's, not hers.
"""

from policyengine_uk.model_api import *


def working_age_applicant_or_partner(person, period):
    """The applicant and partner whose means are assessed."""
    return person("is_council_tax_reduction_applicant_or_partner", period)


def applicant_family(benunit, period):
    """Whether the benefit unit's partner, children and awards are the
    applicant's: false where the household head applies alone."""
    return ~benunit("council_tax_reduction_head_applies_alone", period)


def working_age_child(person, period):
    """A child or young person in the applicant's family, under the scheme's
    own young person definition (the Universal Credit one in Scotland's
    working-age scheme from 2022-23, Child Benefit's elsewhere)."""
    return person(
        "is_child_or_young_person_for_council_tax_reduction", period
    ) & ~person.benunit("council_tax_reduction_head_applies_alone", period)


def working_age_couple(benunit, period):
    return applicant_family(benunit, period) & benunit("is_couple", period)


def working_age_lone_parent(benunit, period):
    return applicant_family(benunit, period) & benunit(
        "is_council_tax_reduction_lone_parent", period
    )


def working_age_adult_premium_conditions(benunit, period, parameters):
    """Whether the applicant's family qualifies for the disability, enhanced
    disability and severe disability premiums, and whether the severe
    disability premium is at the double rate.

    Who qualifies follows the model's legacy premium variables, with Council
    Tax Reduction's own severe disability premium family test
    (council_tax_reduction_severe_disability_premium). Where the household
    head applies alone, the conditions are the head's own as a single person,
    as in council_tax_reduction_premiums.
    """
    dwp = parameters(period).gov.dwp.disability_premia
    disability = benunit("disability_premium", period) > 0
    enhanced = benunit("enhanced_disability_premium", period) > 0
    severe_weekly = (
        benunit("council_tax_reduction_severe_disability_premium", period)
        / WEEKS_IN_YEAR
    )
    severe = severe_weekly > 0
    # The legacy variable pays either the single or the double rate; follow
    # whichever it chose.
    severe_double = severe_weekly > (dwp.severe_single + dwp.severe_couple) / 2

    head_applies_alone = ~applicant_family(benunit, period)
    person = benunit.members
    head = working_age_applicant_or_partner(person, period) & benunit.project(
        head_applies_alone
    )

    def head_has(condition):
        return benunit.any(head & condition)

    # The severe disability premium's non-dependants, as in
    # council_tax_reduction_premiums: every resident aged 18 or over outside
    # the head's family (the head alone) who neither receives a qualifying
    # benefit nor is blind.
    counted = (
        (person("age", period) >= dwp.severe_non_dependant_age)
        & ~person("receives_severe_disability_premium_qualifying_benefit", period)
        & ~person("is_blind", period)
    )
    others_counted = benunit.max(person.household.sum(counted)) - benunit.sum(
        counted & head
    )
    head_severe = head_has(
        person("receives_severe_disability_premium_qualifying_benefit", period)
        & ~person("is_cared_for_by_carer_benefit_recipient", period)
    ) & (others_counted == 0)
    return (
        where(
            head_applies_alone,
            head_has(person("is_disabled_for_benefits", period)),
            disability,
        ),
        where(
            head_applies_alone,
            head_has(person("is_enhanced_disabled_for_benefits", period)),
            enhanced,
        ),
        where(head_applies_alone, head_severe, severe),
        ~head_applies_alone & severe_double,
    )
