from policyengine_uk.model_api import *


class income_support_reported(Variable):
    value_type = float
    entity = Person
    label = "Income Support (reported amount)"
    definition_period = YEAR
    unit = GBP


class would_claim_IS(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Income Support"
    documentation = (
        "Whether this family would claim Income Support if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reported_is = add(benunit, period, ["income_support_reported"]) > 0
        claims_all_entitled_benefits = benunit(
            "claims_all_entitled_benefits", period
        )
        baseline = benunit("baseline_income_support_entitlement", period) > 0
        eligible = benunit("income_support_entitlement", period) > 0
        takeup_rate = parameters(period).gov.dwp.housing_benefit.takeup
        return select(
            [reported_is | claims_all_entitled_benefits, ~baseline & eligible],
            [True, random(benunit) < takeup_rate],
            default=False,
        )


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
            "pension_income",
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


class income_support_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether eligible for Income Support"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        youngest_child_5_or_under = benunit("youngest_child_age", period) <= 5
        lone_parent = benunit("is_lone_parent", period)
        lone_parent_with_young_child = lone_parent & youngest_child_5_or_under
        has_carers = add(benunit, period, ["is_carer_for_benefits"]) > 0
        none_SP_age = ~benunit.any(benunit.members("is_SP_age", period))
        has_ESA_income = benunit("ESA_income", period) > 0
        already_claiming = (
            add(benunit, period, ["income_support_reported"]) > 0
        )
        return (
            (has_carers | lone_parent_with_young_child)
            & none_SP_age
            & ~has_ESA_income
            & already_claiming
        )


class income_support_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable amount of Income Support"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        IS = parameters(period).gov.dwp.income_support
        amounts = IS.amounts
        younger_age = benunit("youngest_adult_age", period)
        older_age = benunit("eldest_adult_age", period)
        younger_under_18 = younger_age < 18
        younger_under_25 = younger_age < 25
        older_under_18 = older_age < 18
        has_children = benunit.any(benunit.members("is_child", period))
        single = benunit("is_single", period)
        single_under_25 = single & ~has_children & younger_under_25
        single_over_25 = single & ~has_children & ~younger_under_25
        lone_young = single & has_children & younger_under_18
        lone_old = single & has_children & ~younger_under_18
        couple_young = ~single & older_under_18
        couple_mixed = ~single & ~older_under_18 & younger_under_18
        couple_old = ~single & ~younger_under_18
        personal_allowance_weekly = select(
            [
                single_under_25,
                single_over_25,
                lone_young,
                lone_old,
                couple_young,
                couple_mixed,
                couple_old,
            ],
            [
                amounts.amount_16_24,
                amounts.amount_over_25,
                amounts.amount_lone_16_17,
                amounts.amount_lone_over_18,
                amounts.amount_couples_16_17,
                amounts.amount_couples_age_gap,
                amounts.amount_couples_over_18,
            ],
        )
        personal_allowance = personal_allowance_weekly * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        return personal_allowance + premiums


class income_support_entitlement(Variable):
    label = "IS entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        amount = benunit("income_support_applicable_amount", period)
        income = benunit("income_support_applicable_income", period)
        eligible = benunit("income_support_eligible", period)
        return max_(0, amount - income) * eligible


class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = "Income Support"
    definition_period = YEAR
    unit = GBP
    defined_for = "would_claim_IS"
    adds = ["income_support_entitlement"]


class baseline_income_support_entitlement(Variable):
    label = "Income Support eligible (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
