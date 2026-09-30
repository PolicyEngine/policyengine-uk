from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.config import (
    is_scotland_scheme,
)


class council_tax_reduction_working_age_earnings_disregard(Variable):
    value_type = float
    entity = BenUnit
    label = "Working-age council tax reduction earnings disregard"
    documentation = (
        "Annual earnings disregarded in a working-age council tax reduction "
        "claim in Scotland or Wales. One weekly disregard applies: £25 for a "
        "lone parent; otherwise £20 where the applicable amount includes a "
        "disability, severe disability or carer premium; otherwise £10 for a "
        "couple and £5 for a single applicant. Applicants without Universal "
        "Credit who meet a work condition have £17.10 more disregarded if "
        "their earnings cover the other disregards, their childcare charges "
        "and the £17.10. Scotland applies the disregards to Universal Credit "
        "earnings too, without the £17.10. A Welsh applicant with Universal "
        "Credit uses the Secretary of State's income figure, which has no "
        "disregards. The disregard is never more than the earnings. The £20 "
        "disregards for special occupations and for permitted work are not "
        "modelled."
    )
    definition_period = YEAR
    unit = GBP
    reference = (
        "https://www.legislation.gov.uk/ssi/2021/249/schedule/3",
        "https://www.legislation.gov.uk/wsi/2013/3029/schedule/8",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.local_authorities
        scotland = is_scotland_scheme(benunit.household("country", period))
        scot = p.scotland.council_tax_reduction.working_age.earnings_disregard
        wales = p.wales.council_tax_reduction.working_age.earnings_disregard

        def rate(name):
            return where(scotland, getattr(scot, name), getattr(wales, name))

        lone_parent = benunit("is_lone_parent", period)
        couple = benunit("is_couple", period)
        disability = (benunit("disability_premium", period) > 0) | (
            benunit("severe_disability_premium", period) > 0
        )
        carer = benunit("carer_premium", period) > 0
        base = select(
            [lone_parent, disability | carer, couple],
            [rate("lone_parent"), rate("disability_or_carer"), rate("couple")],
            rate("single"),
        )

        person = benunit.members
        claimant_or_partner = person("is_claimant_or_partner", period)
        hours = person("weekly_hours", period)
        age = person("age", period)
        in_work = benunit.any(
            claimant_or_partner
            & (hours >= benunit.project(rate("remunerative_work_hours")))
        )
        full_time_25_or_over = benunit.any(
            claimant_or_partner
            & (hours >= benunit.project(rate("additional_full_time_hours")))
            & (age >= benunit.project(rate("additional_full_time_age")))
        )
        children = benunit.sum(
            person("is_child_or_young_person_for_legacy_benefits", period)
        )
        work_condition = (
            full_time_25_or_over
            | (couple & (children > 0) & in_work)
            | (lone_parent & in_work)
            | ((benunit("disability_premium", period) > 0) & in_work)
        )
        earnings = benunit("council_tax_reduction_working_age_earned_income", period)
        childcare = benunit(
            "council_tax_reduction_working_age_childcare_deduction", period
        )
        additional = rate("additional")
        covers_additional = earnings >= (base + additional) * WEEKS_IN_YEAR + childcare
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        additional_applies = work_condition & covers_additional & ~has_universal_credit
        weekly = base + additional * additional_applies
        weekly = where(has_universal_credit & ~scotland, 0, weekly)
        return min_(earnings, weekly * WEEKS_IN_YEAR)
