from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class ESA_income_reported(Variable):
    value_type = float
    entity = BenUnit
    label = u"ESA (income-based) (reported amount per week)"
    definition_period = YEAR


class ESA_income_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for ESA (income-based)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        eligible = benunit("disability_premium", period, options=[MATCH]) > 0
        under_SP_age = benunit.max(benunit.members("is_SP_age", period)) == 0
        eligible *= under_SP_age
        already_claiming = (
            benunit("ESA_income_reported", period, options=[MATCH])
            + aggr(benunit, period, ["ESA_contrib"], options=[MATCH])
            > 0
        )
        return eligible


class ESA_income_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable amount of ESA (income-based)"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        ESA_income = parameters(period).benefits.ESA.income
        younger_age = benunit("youngest_adult_age", period.this_year)
        older_age = benunit("eldest_adult_age", period.this_year)
        personal_allowance = (
            benunit("is_single", period)
            * (
                (younger_age < 25) * ESA_income.amount_18_24
                + (younger_age >= 25) * ESA_income.amount_over_25
            )
            + benunit("is_couple", period) * ESA_income.couple
        )
        premiums = (
            benunit("severe_disability_premium", period)
            + benunit("enhanced_disability_premium", period)
            + benunit("carer_premium", period)
        )
        return (personal_allowance + premiums) * benunit(
            "ESA_income_eligible", period.this_year
        )


class ESA_income_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Relevant income for ESA (income-based)"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        ESA_income = parameters(period).benefits.ESA.income
        BENUNIT_MEANS_TESTED_BENEFITS = ["child_tax_credit"]
        PERSON_MEANS_TESTED_BENEFITS = ["JSA_contrib"]
        benefits = aggr(
            benunit, period, PERSON_MEANS_TESTED_BENEFITS, options=[MATCH]
        ) + add(
            benunit, period, BENUNIT_MEANS_TESTED_BENEFITS, options=[MATCH]
        )
        means_tested_income = (
            benunit("benunit_post_tax_income", period, options=[MATCH])
            + benefits
        ) - benunit.sum(
            benunit.members("pension_contributions", period, options=[MATCH])
        )
        income = max_(
            0,
            means_tested_income
            - benunit("is_single_person", period)
            * ESA_income.income_disregard_single
            - benunit("is_couple", period) * ESA_income.income_disregard_couple
            - benunit("is_lone_parent", period)
            * ESA_income.income_disregard_lone_parent,
        )
        return income


class ESA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"ESA (income-based)"
    definition_period = WEEK

    def formula(benunit, period, parameters):
        return benunit("ESA_income_reported", period.this_year)