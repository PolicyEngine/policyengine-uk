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

        def pensioner_allowance(category):
            # Existing 30-April fiscal-year convention: the raw GB category
            # ends on 6 December 2018; NI's replacement table is April 2019.
            # Neither date is a new claimant-history input. A zero reform of
            # the lower amount must remain zero, not fall back to the higher.
            lower = category.aged_under_65
            age_limit = where(
                northern_ireland,
                lower.age_limit_northern_ireland,
                lower.age_limit_great_britain,
            )
            return where(eldest_age < age_limit, lower.amount, category.aged)

        single_personal_allowance = (
            u_25 * p.single.younger
            + o_25 * p.single.older
            + pension_age_regulations * pensioner_allowance(p.single)
        )
        couple_personal_allowance = (
            u_18 * p.couple.younger
            + o_18 * p.couple.older
            + pension_age_regulations * pensioner_allowance(p.couple)
        )
        lone_parent_personal_allowance = (
            u_18 * p.lone_parent.younger
            + o_18 * p.lone_parent.older
            + pension_age_regulations * pensioner_allowance(p.lone_parent)
        )
        personal_allowance = (
            single * single_personal_allowance
            + couple * couple_personal_allowance
            + lone_parent * lone_parent_personal_allowance
        ) * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        return personal_allowance + premiums
