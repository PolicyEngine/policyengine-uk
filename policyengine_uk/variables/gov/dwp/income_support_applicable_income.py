from policyengine_uk.model_api import *


class income_support_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for Income Support means test"
    documentation = (
        "Income taken into account for Income Support. Income derived from "
        "capital, such as rent from property, interest and dividends, is "
        "treated as capital from the date it is due (regulation 48(4)) and "
        "disregarded as income (Schedule 9 paragraph 22); the capital counts "
        "through the capital limit and tariff income. Tax on that income is "
        "not deducted, as Schedule 9 paragraph 1 disregards tax only on income "
        "taken into account. Rent for letting part of the home stays income, "
        "less the paragraph 19 disregard. Rent from other premises whose value "
        "is disregarded (Schedule 10 paragraphs 2, 4 and 25 to 28) also stays "
        "income, but the model cannot identify those premises."
    )
    definition_period = YEAR
    unit = GBP
    reference = [
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/40",
        "https://www.legislation.gov.uk/uksi/1987/1967/regulation/48",
        "https://www.legislation.gov.uk/uksi/1987/1967/schedule/9",
    ]

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "private_pension_income",
            "legacy_benefits_home_letting_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            INCOME_COMPONENTS.append("basic_income")
        income = add(benunit, period, INCOME_COMPONENTS)
        tax = add(
            benunit,
            period,
            ["legacy_means_test_income_tax", "national_insurance"],
        )
        income += add(benunit, period, ["social_security_income"])
        income += benunit("income_support_tariff_income", period)
        income -= tax
        income -= add(benunit, period, ["pension_contributions"]) * 0.5
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        # Calculate income disregards for each family type.
        mt = IS.means_test
        single = family_type == families.SINGLE
        income_disregard_single = single * mt.income_disregard_single
        single = family_type == families.SINGLE
        income_disregard_couple = (
            benunit("is_couple", period) * mt.income_disregard_couple
        )
        lone_parent = family_type == families.LONE_PARENT
        income_disregard_lone_parent = lone_parent * mt.income_disregard_lone_parent
        income_disregard = (
            income_disregard_single
            + income_disregard_couple
            + income_disregard_lone_parent
        ) * WEEKS_IN_YEAR
        return max_(0, income - income_disregard)
