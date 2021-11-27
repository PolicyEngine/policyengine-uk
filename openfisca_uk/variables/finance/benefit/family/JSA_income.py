from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class JSA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"JSA (income-based) (reported amount)"
    definition_period = YEAR


class JSA_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for JSA (income-based)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        JSA = parameters(period).benefit.JSA
        hours = benunit("benunit_weekly_hours", period)
        eligible = benunit("is_single", period) * (
            hours < JSA.hours.single
        ) + benunit("is_couple", period) * (hours < JSA.hours.couple)
        under_SP_age = benunit.min(benunit.members("is_SP_age", period)) == 0
        eligible *= under_SP_age
        employment_statuses = benunit.members("employment_status", period)
        one_unemployed = benunit.any(
            employment_statuses
            == employment_statuses.possible_values.UNEMPLOYED
        )
        eligible *= (
            not_(benunit("income_support", period) > 0) * one_unemployed
        )
        return eligible


class JSA_income_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"Maximum amount of JSA (income-based)"
    definition_period = YEAR
    reference = "Jobseekers Act 1995 s. 4"

    def formula(benunit, period, parameters):
        JSA = parameters(period).benefit.JSA
        age = benunit("youngest_adult_age", period)
        personal_allowance = (
            benunit("is_single", period)
            * (
                (age < 25) * JSA.income.amount_18_24
                + (age >= 25) * JSA.income.amount_over_25
            )
            + benunit("is_couple", period) * JSA.income.couple
        ) * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        return (
            (personal_allowance + premiums)
            * benunit("JSA_income_eligible", period)
            * benunit("claims_JSA", period)
        )


class would_claim_JSA(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Would claim income-based JSA"
    documentation = (
        "Whether this family would claim income-based JSA if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return (
            random(benunit) <= parameters(period).benefit.JSA.income.takeup
        ) + benunit("claims_all_entitled_benefits", period)


class claims_JSA(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether this family is imputed to claim JSA based on survey response and take-up rates"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("would_claim_JSA", period) & benunit(
            "claims_legacy_benefits", period
        )


class JSA_income_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Relevant income for JSA (income-based) means test"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        JSA = parameters(period).benefit.JSA
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "property_income",
            "pension_income",
        ]
        income = aggr(benunit, period, INCOME_COMPONENTS)
        tax = aggr(
            benunit,
            period,
            ["income_tax", "national_insurance"],
        )
        income += aggr(benunit, period, ["social_security_income"])
        income -= tax
        income -= aggr(benunit, period, ["pension_contributions"]) * 0.5
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        income = max_(
            0,
            income
            - (family_type == families.SINGLE)
            * JSA.income.income_disregard_single
            * WEEKS_IN_YEAR
            - benunit("is_couple", period)
            * JSA.income.income_disregard_couple
            * WEEKS_IN_YEAR
            - (family_type == families.LONE_PARENT)
            * JSA.income.income_disregard_lone_parent
            * WEEKS_IN_YEAR,
        )
        return income


class JSA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"JSA (income-based)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        amount = benunit("JSA_income_applicable_amount", period)
        income = benunit("JSA_income_applicable_income", period)
        claims_JSA = benunit("claims_JSA", period)
        return (
            max_(
                0,
                (amount - income),
            )
            * claims_JSA
            * benunit("JSA_income_eligible", period)
        )


class JSA(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Jobseeker's Allowance for this family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["JSA_contrib"]) + benunit(
            "JSA_income", period
        )
