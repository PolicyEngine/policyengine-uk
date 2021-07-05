from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class housing_benefit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Housing Benefit (reported amount)"
    definition_period = YEAR


class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Housing Benefit for the family"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["housing_benefit_reported"])


class housing_benefit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for Housing Benefit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        social = benunit.any(benunit.members("in_social_housing", period))
        return social + benunit("LHA_eligible", period)


class claims_HB(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether this family is imputed to claim Housing Benefit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        already_claiming = (
            aggr(
                benunit,
                period,
                ["housing_benefit_reported"],
            )
            > 0
        )
        would_claim = benunit("claims_legacy_benefits", period) * (
            random(benunit) < parameters(period).benefit.housing_benefit.takeup
        )
        return already_claiming + would_claim


class housing_benefit_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable amount for Housing Benefit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        HB = parameters(period).benefit.housing_benefit
        PA = HB.allowances
        one_over_SP_age = benunit.any(benunit.members("is_SP_age", period))
        eldest_age = benunit("eldest_adult_age", period)
        u_18 = eldest_age < 18
        u_25 = eldest_age < 25
        o_25 = (eldest_age >= 25) * not_(one_over_SP_age)
        o_18 = (eldest_age >= 18) * not_(one_over_SP_age)
        single = benunit("is_single_person", period)
        couple = benunit("is_couple", period)
        lone_parent = benunit("is_lone_parent", period)
        personal_allowance = (
            single
            * (
                u_25 * PA.single.under_25
                + o_25 * PA.single.over_25
                + one_over_SP_age * PA.single.SP_age
            )
            + couple
            * (
                u_18 * PA.couple.both_under_18
                + o_18 * PA.couple.over_18
                + one_over_SP_age * PA.couple.SP_age
            )
            + lone_parent
            * (
                u_18 * PA.lone_parent.under_18
                + o_18 * PA.lone_parent.over_18
                + one_over_SP_age * PA.lone_parent.SP_age
            )
        ) * WEEKS_IN_YEAR
        premiums = benunit("benefits_premiums", period)
        return (personal_allowance + premiums) * benunit(
            "housing_benefit_eligible", period
        )


class housing_benefit_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Relevant income for Housing Benefit means test"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        means_test = parameters(period).benefit.housing_benefit.means_test
        BENUNIT_MEANS_TESTED_BENEFITS = [
            "child_benefit",
            "income_support",
            "JSA_income",
            "ESA_income",
        ]
        INCOME_COMPONENTS = [
            "employment_income",
            "trading_income",
            "property_income",
            "pension_income",
        ]
        benefits = add(benunit, period, BENUNIT_MEANS_TESTED_BENEFITS)
        income = aggr(benunit, period, INCOME_COMPONENTS)
        tax = aggr(
            benunit,
            period,
            ["income_tax", "national_insurance"],
        )
        income += aggr(benunit, period, ["personal_benefits"])
        income += add(benunit, period, ["tax_credits"])
        income -= tax
        income -= aggr(benunit, period, ["pension_contributions"]) * 0.5
        income += benefits
        num_children = benunit.nb_persons(BenUnit.CHILD)
        max_childcare_amount = (
            num_children == 1
        ) * WTC.elements.childcare_1 * WEEKS_IN_YEAR + (
            num_children > 1
        ) * WTC.elements.childcare_2 * WEEKS_IN_YEAR
        childcare_element = min_(
            max_childcare_amount,
            benunit.sum(benunit.members("childcare_cost", period)),
        )
        applicable_income = max_(
            0,
            income
            - benunit("is_single_person", period)
            * means_test.income_disregard_single
            * WEEKS_IN_YEAR
            - benunit("is_couple", period)
            * means_test.income_disregard_couple
            * WEEKS_IN_YEAR
            - benunit("is_lone_parent", period)
            * means_test.income_disregard_lone_parent
            * WEEKS_IN_YEAR
            - (
                (
                    benunit.sum(benunit.members("weekly_hours", period))
                    > means_test.worker_hours
                )
                + (
                    benunit("is_lone_parent", period)
                    * benunit.sum(benunit.members("weekly_hours", period))
                    > WTC.min_hours.lower
                )
            )
            * means_test.worker_income_disregard
            * WEEKS_IN_YEAR
            - childcare_element,
        )
        return applicable_income


class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Housing Benefit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        rent = benunit.max(benunit.members.household("rent", period))
        LHA = benunit("LHA_eligible", period.this_year)
        applicable_amount = benunit(
            "housing_benefit_applicable_amount", period
        )
        income = benunit("housing_benefit_applicable_income", period)
        withdrawal_rate = parameters(
            period
        ).benefit.housing_benefit.means_test.withdrawal_rate
        final_amount = max_(
            0, rent - max_(0, income - applicable_amount) * withdrawal_rate
        )
        amount = where(
            LHA, min_(final_amount, benunit("LHA_cap", period)), final_amount
        )
        other_capped_benefits = add(
            benunit,
            period,
            [
                "child_benefit",
                "child_tax_credit",
                "JSA_income",
                "income_support",
                "ESA_income",
            ],
        ) + aggr(
            benunit,
            period,
            ["JSA_contrib", "incapacity_benefit", "ESA_contrib", "SDA"],
        )
        final_amount = min_(
            amount * benunit("claims_HB", period),
            benunit("benefit_cap", period) - other_capped_benefits,
        )
        return final_amount
