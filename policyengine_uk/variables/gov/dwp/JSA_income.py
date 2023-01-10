from policyengine_uk.model_api import *


class JSA_income_reported(Variable):
    value_type = float
    entity = Person
    label = "JSA (income-based) (reported amount)"
    definition_period = YEAR
    unit = GBP


class JSA_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Eligibility for income-based JSA"
    documentation = "Whether the benefit unit is eligible for income-based Jobseekers' Allowance"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # Calculate work hours eligibility.
        hours_limit = parameters(period).gov.dwp.JSA.hours
        hours = benunit("benunit_weekly_hours", period)
        single = benunit("is_single", period)
        hours_eligible_as_single = single & (hours < hours_limit.single)
        couple = benunit("is_couple", period)
        hours_eligible_as_couple = couple & (hours < hours_limit.couple)
        hours_eligible = hours_eligible_as_single | hours_eligible_as_couple
        # Benefit units with state pension age people are ineligible.
        all_under_SP_age = ~benunit.any(benunit.members("is_SP_age", period))
        # Must have at least one unemployed person.
        employment_statuses = benunit.members("employment_status", period)
        unemployed_members = (
            employment_statuses
            == employment_statuses.possible_values.UNEMPLOYED
        )
        any_unemployed = benunit.any(unemployed_members)
        # Cannot claim Income Support.
        not_on_income_support = benunit("income_support", period) == 0
        already_claiming = add(benunit, period, ["JSA_income_reported"]) > 0
        return (
            hours_eligible
            & all_under_SP_age
            & any_unemployed
            & not_on_income_support
            & already_claiming
        )


class JSA_income_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Maximum amount of JSA (income-based)"
    documentation = "Maximum amount of income-based Jobseeker's Allowance"
    definition_period = YEAR
    reference = "Jobseekers Act 1995 s. 4"
    unit = GBP

    def formula(benunit, period, parameters):
        income = parameters(period).gov.dwp.JSA.income
        age = benunit("youngest_adult_age", period)
        single = benunit("is_single", period)
        couple = benunit("is_couple", period)
        single_18_24 = single & (age < 25)
        single_over_25 = single & (age >= 25)
        pa_single_18_24 = single_18_24 * income.amount_18_24
        pa_single_over_25 = single_over_25 * income.amount_over_25
        pa_couple = couple * income.couple
        weekly_personal_allowance = (
            pa_single_18_24 + pa_single_over_25 + pa_couple
        )
        personal_allowance = weekly_personal_allowance * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        amount_if_claims = personal_allowance + premiums
        eligible = benunit("JSA_income_eligible", period)
        claims = benunit("would_claim_JSA", period)
        return amount_if_claims * eligible * claims


class would_claim_JSA(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim income-based JSA"
    documentation = (
        "Whether this family would claim income-based JSA if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return add(benunit, period, ["JSA_income_reported"]) > 0


class JSA_income_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Relevant income for JSA (income-based) means test"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        JSA = parameters(period).gov.dwp.JSA
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
        # Calculate disregard.
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        single = family_type == families.SINGLE
        single_disregard = single * JSA.income.income_disregard_single
        couple = benunit("is_couple", period)
        couple_disregard = couple * JSA.income.income_disregard_couple
        lone_parent = family_type == families.LONE_PARENT
        lone_parent_disregard = (
            lone_parent * JSA.income.income_disregard_lone_parent
        )
        weekly_disregard = (
            single_disregard + couple_disregard + lone_parent_disregard
        )
        disregard = weekly_disregard * WEEKS_IN_YEAR
        return max_(0, income - disregard)


class JSA_income(Variable):
    value_type = float
    entity = BenUnit
    label = "JSA (income-based)"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        applicable_amount = benunit("JSA_income_applicable_amount", period)
        applicable_income = benunit("JSA_income_applicable_income", period)
        amount_if_claims = max_(0, applicable_amount - applicable_income)
        claims = benunit("would_claim_JSA", period)
        eligible = benunit("JSA_income_eligible", period)
        return amount_if_claims * claims * eligible


class JSA(Variable):
    value_type = float
    entity = BenUnit
    label = "Amount of Jobseeker's Allowance for this family"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        JSA_contrib = add(benunit, period, ["JSA_contrib"])
        JSA_income = benunit("JSA_income", period)
        return JSA_contrib + JSA_income
