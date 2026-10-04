from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.local_authorities.council_tax_reduction.working_age._applicant import (
    working_age_applicant_or_partner,
)
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
        "lone parent; otherwise £20 of the family's earnings where the "
        "applicable amount includes a disability or severe disability "
        "premium (in Scotland also for a Universal Credit applicant with "
        "limited capability for work who is in employment); otherwise, with a "
        "carer benefit in payment, £20 of the carers' own "
        "earnings, plus up to £10 of a non-carer partner's earnings within the "
        "same £20. In Scotland, where the carer premium is included but no "
        "one in the family has a carer benefit in payment (an award of "
        "Universal Credit with the carer element, or a carer benefit an "
        "overlapping benefit reduces to nil), the £20 is approximated against "
        "the family's earnings, which can exceed the £10 limit on a non-carer "
        "partner's earnings. Otherwise £10 for a couple and £5 for a single "
        "applicant. "
        "Applicants without Universal Credit who meet a work condition have "
        "£17.10 more disregarded if their earnings cover the other disregard, "
        "their childcare charges and the £17.10; for a couple's disability "
        "condition, the disabled member must be the one in remunerative work, "
        "and in Scotland from April 2022 only employed earnings count. "
        "Scotland applies the disregards to Universal Credit earnings too, "
        "without the £17.10. A Welsh applicant with Universal Credit uses the "
        "Secretary of State's income figure, which has no disregards. The "
        "disregard is never more than the earnings. The £20 disregards for "
        "special occupations and permitted work are not modelled."
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

        person = benunit.members
        claimant_or_partner = working_age_applicant_or_partner(person, period)
        weekly_person_earnings = (
            person("council_tax_reduction_working_age_person_earned_income", period)
            / WEEKS_IN_YEAR
        )
        earnings = benunit("council_tax_reduction_working_age_earned_income", period)
        weekly_earnings = earnings / WEEKS_IN_YEAR

        lone_parent = benunit("is_lone_parent", period)
        couple = benunit("is_couple", period)
        has_universal_credit = benunit(
            "council_tax_reduction_working_age_has_universal_credit", period
        )
        # Scotland also gives the £20 to a Universal Credit applicant or
        # partner with limited capability for work (or for work-related
        # activity) where one of them is under pensionable age and in
        # employment (SSI 2021/249 Sch 3 para 4(3)).
        scottish_uc_limited_capability = (
            scotland
            & has_universal_credit
            & benunit.any(
                claimant_or_partner & person("uc_limited_capability_for_WRA", period)
            )
            & benunit.any(
                claimant_or_partner
                & ~person("is_SP_age", period)
                & (weekly_person_earnings > 0)
            )
        )
        disability = (
            (benunit("disability_premium", period) > 0)
            | (benunit("severe_disability_premium", period) > 0)
            | scottish_uc_limited_capability
        )
        # The carer disregard needs a carer benefit in payment (Wales Sch 8
        # para 6: "in receipt of carer's allowance"); in Scotland an award of
        # Universal Credit with the carer element also qualifies.
        carers = benunit("council_tax_reduction_working_age_carers", period)
        # Carer disregard: £20 of the carers' own earnings, plus up to £10 of a
        # non-carer partner's earnings within the £20 (Wales Sch 8 paras 6-7;
        # Scotland Sch 3 paras 6-7). Carers are identified by carer benefit
        # receipt. A Scottish carer premium with no carer benefit in payment
        # in the family (a UC carer element, or a benefit overlapped to nil)
        # falls back to the family's earnings, an approximation.
        is_carer = claimant_or_partner & person("receives_carer_benefit", period)
        carer_earnings = benunit.sum(is_carer * weekly_person_earnings)
        other_earnings = benunit.sum(
            (claimant_or_partner & ~is_carer) * weekly_person_earnings
        )
        named_carers = benunit.sum(is_carer)
        carer_cap = rate("disability_or_carer")
        partner_cap = rate("couple")
        carer_disregard = where(
            named_carers == 0,
            min_(carer_cap, weekly_earnings),
            where(
                couple & (named_carers == 1),
                min_(carer_cap, carer_earnings + min_(partner_cap, other_earnings)),
                min_(carer_cap, carer_earnings),
            ),
        )
        base = select(
            [
                lone_parent,
                disability,
                (named_carers > 0) | (scotland & (carers > 0)),
                couple,
            ],
            [
                min_(rate("lone_parent"), weekly_earnings),
                min_(rate("disability_or_carer"), weekly_earnings),
                carer_disregard,
                min_(rate("couple"), weekly_earnings),
            ],
            min_(rate("single"), weekly_earnings),
        )

        hours = person("weekly_hours", period)
        age = person("age", period)
        remunerative = hours >= benunit.project(rate("remunerative_work_hours"))
        in_work = benunit.any(claimant_or_partner & remunerative)
        full_time_25_or_over = benunit.any(
            claimant_or_partner
            & (hours >= benunit.project(rate("additional_full_time_hours")))
            & (age >= benunit.project(rate("additional_full_time_age")))
        )
        # For a couple, the member in remunerative work must be the one who
        # meets the disability premium conditions (Wales Sch 8 para
        # 18(2)(b)(v); Scotland Sch 3 para 15(2)(b)(iv)).
        disabled_worker = benunit.any(
            claimant_or_partner
            & person("is_disabled_for_benefits", period)
            & remunerative
        )
        children = benunit.sum(
            person("is_child_or_young_person_for_legacy_benefits", period)
        )
        work_condition = (
            full_time_25_or_over
            | (couple & (children > 0) & in_work)
            | (lone_parent & in_work)
            | ((benunit("disability_premium", period) > 0) & disabled_worker)
        )
        childcare = benunit(
            "council_tax_reduction_working_age_childcare_deduction", period
        )
        additional = rate("additional")
        employed_only = scotland & (scot.additional_employed_earnings_only > 0)
        employed = benunit(
            "council_tax_reduction_working_age_employed_earned_income", period
        )
        tested_earnings = where(employed_only, employed, earnings)
        covers_additional = (tested_earnings > 0) & (
            tested_earnings >= (base + additional) * WEEKS_IN_YEAR + childcare
        )
        additional_applies = work_condition & covers_additional & ~has_universal_credit
        weekly = base + additional * additional_applies
        weekly = where(has_universal_credit & ~scotland, 0, weekly)
        return min_(earnings, weekly * WEEKS_IN_YEAR)
