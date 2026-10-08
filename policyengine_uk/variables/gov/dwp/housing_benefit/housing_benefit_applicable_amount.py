from policyengine_uk.model_api import *
from policyengine_uk.utils.excise import fiscal_year_segments


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
        "https://www.legislation.gov.uk/uksi/2006/213/schedule/3/paragraph/1A",
        "https://www.legislation.gov.uk/uksi/2017/1187/regulation/7/made",
        "https://www.legislation.gov.uk/nisr/2017/242/regulation/7/made",
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
        # Schedule 3 paragraph 1A tests the claimant personally, not a partner.
        person = benunit.members
        esa_exception = benunit.any(
            person("is_housing_benefit_claimant", period)
            & person("esa_main_phase", period)
        )
        older_single = (eldest_age >= older_age_threshold) | esa_exception
        older_family = (eldest_age >= younger_age_threshold) | esa_exception
        single = benunit("is_single_person", period)
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        working_age = (
            single * where(older_single, p.single.older, p.single.younger)
            + couple * where(older_family, p.couple.older, p.couple.younger)
            + lone_parent
            * where(older_family, p.lone_parent.older, p.lone_parent.younger)
        )
        pension_age = 0
        for rules, share in fiscal_year_segments(
            parameters.gov.dwp.housing_benefit.allowances.pension_age_history,
            period.start.year,
        ):
            lower = rules.under_65_category_applies & (
                eldest_age < p.age_threshold.former_pension_age
            )
            pension_age += share * (
                single * where(lower, p.single.pension_age_under_65, p.single.aged)
                + couple * where(lower, p.couple.pension_age_under_65, p.couple.aged)
                + lone_parent
                * where(lower, p.lone_parent.pension_age_under_65, p.lone_parent.aged)
            )
        personal_allowance = (
            where(pension_age_regulations, pension_age, working_age) * WEEKS_IN_YEAR
        )
        premiums = benunit("benefits_premiums", period)
        children = benunit("housing_benefit_child_allowance", period)
        return (
            personal_allowance
            + children
            + premiums
            + benunit("housing_benefit_family_premium", period)
            + benunit("housing_benefit_child_disability_premiums", period)
        )
