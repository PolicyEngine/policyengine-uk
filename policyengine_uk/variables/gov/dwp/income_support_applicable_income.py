from policyengine_uk.model_api import *


class income_support_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for Income Support means test"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "private_pension_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            INCOME_COMPONENTS.append("basic_income")
        income = add(benunit, period, INCOME_COMPONENTS)
        tax = add(
            benunit,
            period,
            ["income_tax", "national_insurance"],
        )
        income += add(benunit, period, ["social_security_income"])
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
        income_disregard_lone_parent = (
            lone_parent * mt.income_disregard_lone_parent
        )
        income_disregard = (
            income_disregard_single
            + income_disregard_couple
            + income_disregard_lone_parent
        ) * WEEKS_IN_YEAR
        return max_(0, income - income_disregard)
