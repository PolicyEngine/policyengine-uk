from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = u"Disability premium"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        dis = parameters(period).benefits.disability_premia
        amount = (benunit("disabled_adults", period.this_year) > 0) * (
            benunit("is_single", period) * dis.disability_single
            + benunit("is_couple", period) * dis.disability_couple
        )
        return amount


class severe_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = u"Severe disability premium"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        dis = parameters(period).benefits.disability_premia
        amount = (
            benunit("severely_disabled_adults", period.this_year) > 0
        ) * (
            benunit("is_single", period) * dis.severe_single
            + benunit("is_couple", period) * dis.severe_couple
        )
        return amount


class enhanced_disability_premium(Variable):
    value_type = float
    entity = BenUnit
    label = u"Enhanced disability premium"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        dis = parameters(period).benefits.disability_premia
        amount = (
            benunit("enhanced_disabled_adults", period.this_year) > 0
        ) * (
            benunit("is_single", period) * dis.enhanced_single
            + benunit("is_couple", period) * dis.enhanced_couple
        )
        return amount


class carer_premium(Variable):
    value_type = float
    entity = BenUnit
    label = u"Carer premium"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return (
            benunit("has_carer", period, options=[MATCH])
            * parameters(period).benefits.carer_premium.single
        )


class JSA_income_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"JSA (income-based) (reported amount per week)"
    definition_period = YEAR


class JSA_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for JSA (income-based)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        JSA = parameters(period).benefits.JSA
        hours = benunit("benunit_hours", period)
        eligible = benunit("is_single", period) * (hours < 16) + benunit(
            "is_couple", period
        ) * (hours < 24)
        under_SP_age = benunit.min(benunit.members("is_SP_age", period)) == 0
        eligible *= under_SP_age
        already_claiming = (
            benunit("JSA_income_reported", period, options=[MATCH]) > 0
        )
        return eligible * already_claiming


class JSA_income_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable amount of JSA (income-based)"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        JSA = parameters(period).benefits.JSA
        age = benunit("youngest_adult_age", period.this_year)
        personal_allowance = (
            benunit("is_single", period)
            * (
                (age < 25) * JSA.contrib.amount_18_24
                + (age >= 25) * JSA.contrib.amount_over_25
            )
            + benunit("is_couple", period) * JSA.income.couple
        )
        premiums = (
            benunit("disability_premium", period)
            + benunit("severe_disability_premium", period)
            + benunit("enhanced_disability_premium", period)
            + benunit("carer_premium", period)
        )
        return (personal_allowance + premiums) * benunit(
            "JSA_income_eligible", period.this_year
        )


class JSA_income_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Relevant income for JSA (income-based) means test"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        JSA = parameters(period).benefits.JSA
        BENUNIT_MEANS_TESTED_BENEFITS = ["working_tax_credit", "child_tax_credit"]
        PERSON_MEANS_TESTED_BENEFITS = ["JSA_contrib"]
        benefits = aggr(
            benunit, period, PERSON_MEANS_TESTED_BENEFITS, options=[MATCH]
        ) + add(
            benunit, period, BENUNIT_MEANS_TESTED_BENEFITS, options=[MATCH]
        )
        means_tested_income = (
            benunit("benunit_post_tax_income", period, options=[MATCH])
            + benefits
        ) - benunit("benunit_pension_contributions", period, options=[MATCH])
        income = max_(
            0,
            means_tested_income
            - benunit("is_single_person", period)
            * JSA.income.income_disregard_single
            - benunit("is_couple", period) * JSA.income.income_disregard_couple
            - benunit("is_lone_parent", period)
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
        return max_(
            0,
            (amount - income),
        )
