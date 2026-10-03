from policyengine_uk.model_api import *


class housing_benefit_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "applicable Housing Benefit amount"
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_eligible"
    reference = "https://www.legislation.gov.uk/uksi/2006/213/schedule/3"

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.allowances
        any_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        eldest_age = benunit("eldest_claimant_or_partner_age", period)
        older_age_threshold = p.age_threshold.older
        younger_age_threshold = p.age_threshold.younger
        u_18 = eldest_age < younger_age_threshold
        u_25 = eldest_age < older_age_threshold
        o_25 = (eldest_age >= older_age_threshold) & ~any_over_SP_age
        o_18 = (eldest_age >= younger_age_threshold) * ~any_over_SP_age
        single = benunit("is_single_person", period)
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        # Pension-age allowances (SI 2006/214 Sch 3 para 1; NI: SR 2006/406
        # Sch 4 para 1). Since 1 April 2021 units whose members all attained
        # State Pension age on or after the cutoff get the lower rates in
        # sub-paragraphs (1)(c) and (2)(c); the rest keep the higher rates.
        if p.pension_age_cutoff is None:
            single_aged, couple_aged, lone_parent_aged = (
                p.single.aged,
                p.couple.aged,
                p.lone_parent.aged,
            )
        else:
            before_cutoff = benunit(
                "housing_benefit_attained_pension_age_before_cutoff", period
            )
            single_aged = where(before_cutoff, p.single.aged, p.single.aged_from_cutoff)
            couple_aged = where(before_cutoff, p.couple.aged, p.couple.aged_from_cutoff)
            lone_parent_aged = where(
                before_cutoff, p.lone_parent.aged, p.lone_parent.aged_from_cutoff
            )
        single_personal_allowance = (
            u_25 * p.single.younger
            + o_25 * p.single.older
            + any_over_SP_age * single_aged
        )
        couple_personal_allowance = (
            u_18 * p.couple.younger
            + o_18 * p.couple.older
            + any_over_SP_age * couple_aged
        )
        lone_parent_personal_allowance = (
            u_18 * p.lone_parent.younger
            + o_18 * p.lone_parent.older
            + any_over_SP_age * lone_parent_aged
        )
        personal_allowance = (
            single * single_personal_allowance
            + couple * couple_personal_allowance
            + lone_parent * lone_parent_personal_allowance
        ) * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        return personal_allowance + premiums
