from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class JSA_income_reported(Variable):
    value_type = float
    entity = Person
    label = u"JSA (income-based) (reported amount per week)"
    definition_period = WEEK


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
        already_claiming = benunit.any(
            benunit.members("JSA_income_reported", period, options=[ADD])
        )
        return eligible * already_claiming


class JSA_income_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"Maximum amount of JSA (income-based)"
    definition_period = WEEK
    reference = "Jobseekers Act 1995 s. 4"

    def formula(benunit, period, parameters):
        JSA = parameters(period).benefit.JSA
        age = benunit("youngest_adult_age", period.this_year)
        personal_allowance = (
            benunit("is_single", period)
            * (
                (age < 25) * JSA.income.amount_18_24
                + (age >= 25) * JSA.income.amount_over_25
            )
            + benunit("is_couple", period) * JSA.income.couple
        )
        premiums = benunit("benefits_premiums", period)
        return (personal_allowance + premiums) * benunit(
            "JSA_income_eligible", period.this_year
        )

class claims_JSA(Variable):
    value_type = bool
    entity = BenUnit
    label = u'Whether this family is imputed to claim JSA based on survey response and take-up rates'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["JSA_income_reported"], options=[ADD]) > 0

class JSA_income_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Relevant income for JSA (income-based) means test"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        JSA = parameters(period).benefit.JSA
        INCOME_COMPONENTS = [
            "employment_income",
            "trading_income",
            "property_income",
            "pension_income"
        ]
        income = aggr(benunit, period, INCOME_COMPONENTS, options=[DIVIDE])
        tax = aggr(benunit, period, ["income_tax", "national_insurance"], options=[DIVIDE])
        income = aggr(benunit, period, ["personal_benefits"])
        income += add(benunit, period, ["child_benefit"])
        income -= aggr(benunit, period, ["pension_contributions"], options=[DIVIDE]) * 0.5
        family_type = benunit("family_type")
        families = family_type.possible_values
        income = max_(
            0,
            income
            - (family_type == families.SINGLE)
            * JSA.income.income_disregard_single
            - benunit("is_couple") * JSA.income.income_disregard_couple
            - (family_type == families.LONE_PARENT)
            * JSA.income.income_disregard_lone_parent,
        )
        return income

class JSA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Job Seeker's Allowance (income-based)"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        amount = benunit("JSA_income_applicable_amount", period)
        income = benunit("JSA_income_applicable_income", period)
        claims_JSA = benunit("claims_JSA", period.this_year)
        return max_(
            0,
            (amount - income),
        ) * claims_JSA

class JSA(Variable):
    value_type = float
    entity = BenUnit
    label = u'Amount of Jobseeker\'s Allowance for this family'
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["JSA_contrib"]) + benunit("JSA_income", period)

class yearly_JSA(Variable):
    value_type = float
    entity = BenUnit
    label = u'Yearly amount of JSA for the family'
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["JSA"], options=[ADD])