from policyengine_uk.model_api import *


class housing_benefit_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "applicable Housing Benefit amount"
    definition_period = YEAR
    unit = GBP
    defined_for = "housing_benefit_eligible"
    reference = (
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3",
        "https://www.legislation.gov.uk/uksi/2006/214/schedule/3",
        "https://www.legislation.gov.uk/uksi/2017/1187/regulation/7",
        "https://www.legislation.gov.uk/nisr/2019/58/schedule/4/made",
        "https://www.legislation.gov.uk/nisr/2017/242/regulation/7/made",
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/1A",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4/part/I",
        "https://www.legislation.gov.uk/nisr/2006/405/schedule/4",
        "https://www.legislation.gov.uk/nisr/2006/406/schedule/4",
        "https://www.legislation.gov.uk/uksi/2015/1857/made",
        "https://www.legislation.gov.uk/nisr/2016/310/made",
    )

    def formula(benunit, period, parameters):
        p = parameters(period).gov.dwp.housing_benefit.allowances
        # Each regulation set has its own Schedule 3 allowance table. Reg 5
        # keeps qualifying-age UC and specified legacy recipients in the
        # working-age regulations, so age alone does not choose the table.
        pension_age_regulations = benunit(
            "housing_benefit_pension_age_regulations_apply", period
        )
        eldest_age = benunit("eldest_claimant_or_partner_age", period)
        older_age_threshold = p.age_threshold.older
        younger_age_threshold = p.age_threshold.younger
        u_18 = eldest_age < younger_age_threshold
        u_25 = eldest_age < older_age_threshold
        o_25 = (eldest_age >= older_age_threshold) & ~pension_age_regulations
        o_18 = (eldest_age >= younger_age_threshold) * ~pension_age_regulations
        single = benunit("is_single_person", period)
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        country = benunit.household("country", period)
        northern_ireland = country == country.possible_values.NORTHERN_IRELAND

        def higher_allowance(category):
            # Until 6 December 2018 (GB, SI 2017/1187 regs 1(2)(b) and 7(7);
            # NI, SR 2017/242 regs 1(2)(b) and 7(7)), units where the claimant
            # and any partner were under 65 got the lower para 1(1)(a) and
            # (2)(a) rates. Read at the existing 30-April fiscal-year convention, with
            # no new claimant-history input. A zero reform of the lower amount
            # stays zero rather than falling back to the higher rate.
            lower = category.aged_under_65
            age_limit = where(
                northern_ireland,
                lower.age_limit_northern_ireland,
                lower.age_limit_great_britain,
            )
            return where(eldest_age < age_limit, lower.amount, category.aged)

        # Pension-age allowances (SI 2006/214 Sch 3 para 1; NI: SR 2006/406
        # Sch 4 para 1). Since 1 April 2021 units whose members all attained
        # State Pension age on or after the cutoff get the lower rates in
        # sub-paragraphs (1)(c) and (2)(c); the rest keep the higher rates.
        single_aged = higher_allowance(p.single)
        couple_aged = higher_allowance(p.couple)
        lone_parent_aged = higher_allowance(p.lone_parent)
        if p.pension_age_cutoff is not None:
            before_cutoff = benunit(
                "housing_benefit_attained_pension_age_before_cutoff", period
            )
            single_aged = where(before_cutoff, single_aged, p.single.aged_from_cutoff)
            couple_aged = where(before_cutoff, couple_aged, p.couple.aged_from_cutoff)
            lone_parent_aged = where(
                before_cutoff, lone_parent_aged, p.lone_parent.aged_from_cutoff
            )
        single_personal_allowance = (
            u_25 * p.single.younger
            + o_25 * p.single.older
            + pension_age_regulations * single_aged
        )
        couple_personal_allowance = (
            u_18 * p.couple.younger
            + o_18 * p.couple.older
            + pension_age_regulations * couple_aged
        )
        lone_parent_personal_allowance = (
            u_18 * p.lone_parent.younger
            + o_18 * p.lone_parent.older
            + pension_age_regulations * lone_parent_aged
        )
        personal_allowance = (
            single * single_personal_allowance
            + couple * couple_personal_allowance
            + lone_parent * lone_parent_personal_allowance
        ) * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        family_premium = benunit("housing_benefit_family_premium", period)
        child_premiums = benunit("housing_benefit_child_disability_premiums", period)
        esa_adjustment = benunit(
            "housing_benefit_main_phase_esa_allowance_adjustment", period
        )
        return (
            personal_allowance
            + premiums
            + family_premium
            + child_premiums
            + esa_adjustment
        )
