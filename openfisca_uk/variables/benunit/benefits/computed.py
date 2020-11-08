from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np


class working_tax_credit_pre_means_test(Variable):
    value_type = float
    entity = BenUnit
    label = (
        u"Working Tax Credit amount received per year, before means testing"
    )
    definition_period = ETERNITY
    reference = [
        "https://www.iser.essex.ac.uk/files/projects/UKMOD/EUROMOD_country_report.pdf#page=25"
    ]

    def formula(benunit, period, parameters):
        hours_worked = benunit.sum(benunit.members("hours_worked", period))
        has_disabled_adult = benunit.max(
            benunit.members("is_adult", period)
            * benunit.members("disabled", period)
        )
        eligible = (
            benunit("is_single", period)
            * (
                hours_worked
                >= parameters(
                    period
                ).benefits.working_tax_credit.hours_requirement_single
            )
            + benunit("is_couple", period)
            * (
                hours_worked
                >= parameters(
                    period
                ).benefits.working_tax_credit.hours_requirement_couple
            )
            + (
                benunit("is_lone_parent", period)
                + benunit("has_worker_over_60", period)
                + has_disabled_adult
                > 0
            )
            * (
                hours_worked
                >= parameters(
                    period
                ).benefits.working_tax_credit.hours_requirement_disadvantaged
            )
        )
        eligible = eligible + benunit("benunit_WTC_reported", period) > 0
        basic_amount = parameters(
            period
        ).benefits.working_tax_credit.basic_element
        works_over_30_hours = (
            hours_worked
            >= parameters(
                period
            ).benefits.working_tax_credit.hours_requirement_single
        )
        premiums = (
            works_over_30_hours
            * parameters(period).benefits.working_tax_credit.worker_element
            + benunit("is_couple", period)
            * parameters(period).benefits.working_tax_credit.couple_element
            + benunit("is_lone_parent", period)
            * parameters(
                period
            ).benefits.working_tax_credit.lone_parent_element
            + benunit.sum(
                benunit.members("is_adult", period)
                * benunit.members("disabled", period)
            )
            * parameters(period).benefits.working_tax_credit.disabled_element
        )
        num_children = benunit.sum(benunit.members("is_child", period))
        max_childcare_amount = (num_children == 1) * parameters(
            period
        ).benefits.working_tax_credit.max_childcare_amount_1 + (
            num_children > 1
        ) * parameters(
            period
        ).benefits.working_tax_credit.max_childcare_amount_over_2
        childcare_element = min_(
            max_childcare_amount,
            parameters(
                period
            ).benefits.working_tax_credit.childcare_element_rate
            * benunit.sum(benunit.members("eligible_childcare_cost", period)),
        )
        total_amount = basic_amount + premiums + childcare_element
        return total_amount * eligible


class child_tax_credit_pre_means_test(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Tax Credit amount received per year, before means testing"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        num_exempt_children = benunit.sum(
            benunit.members("is_CTC_child_limit_exempt", period)
        )
        non_exempt_children = (
            benunit.nb_persons(BenUnit.CHILD) - num_exempt_children
        )
        spaces_left = max_(0, 2 - num_exempt_children)
        children_eligible = num_exempt_children + min_(
            spaces_left, non_exempt_children
        )
        num_disabled_children = benunit.sum(
            benunit.members("is_child", period)
            * benunit.members("disabled", period)
        )
        yearly_amount = (
            parameters(period).benefits.child_tax_credit.family_element
            + parameters(period).benefits.child_tax_credit.child_element
            * children_eligible
            + parameters(
                period
            ).benefits.child_tax_credit.disabled_child_element
            * num_disabled_children
        )
        return yearly_amount * (children_eligible > 0)


class tax_credit_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child and Working Tax Credit amount reduced per week from means testing"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        child_tax_credit_amount = benunit(
            "child_tax_credit_pre_means_test", period
        )
        working_tax_credit_amount = benunit(
            "working_tax_credit_pre_means_test", period
        )
        eligible_for_both = (child_tax_credit_amount > 0) * (
            working_tax_credit_amount > 0
        )
        CTC_only = (child_tax_credit_amount > 0) * (1 - eligible_for_both)
        threshold = (
            eligible_for_both
            * parameters(period).benefits.working_tax_credit.income_threshold
            + CTC_only
            * parameters(
                period
            ).benefits.child_tax_credit.income_threshold_CTC_only
        )
        means_tested_SSP = max_(
            0,
            benunit.sum(benunit.members("SSP", period))
            - parameters(period).benefits.working_tax_credit.SSP_disregard,
        )
        means_tested_earnings = (
            benunit("benunit_earnings", period) + means_tested_SSP
        )
        means_tested_SP = max_(
            0,
            benunit("benunit_state_pension", period)
            + benunit("benunit_pension_income", period)
            - parameters(period).benefits.working_tax_credit.pension_disregard,
        )
        means_tested_benefit_income = benunit.sum(
            benunit.members("incapacity_benefit_reported", period)
        )
        means_tested_income = (
            means_tested_earnings
            + means_tested_SP
            + means_tested_SSP
            + means_tested_benefit_income
            + benunit.sum(
                benunit.members("untaxed_means_tested_bonus", period)
            )
            + benunit.sum(benunit.members("taxed_means_tested_bonus", period))
        )
        reduction = (
            max_(0, (means_tested_income * 52 - threshold))
            * parameters(
                period
            ).benefits.working_tax_credit.income_reduction_rate
        )
        return reduction


class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Working Tax Credit received per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (
            max_(
                0,
                benunit("working_tax_credit_pre_means_test", period)
                - benunit("tax_credit_reduction", period),
            )
            * (benunit("benunit_WTC_reported", period) > 0)
            * (benunit("benunit_universal_credit_reported", period) == 0)
            / 52
        )


class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Child Tax Credit received per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        reduction_left = min_(
            0,
            benunit("working_tax_credit_pre_means_test", period)
            - benunit("tax_credit_reduction", period),
        )
        return (
            max_(
                0,
                benunit("child_tax_credit_pre_means_test", period)
                + reduction_left,
            )
            * (benunit("benunit_CTC_reported", period) > 0)
            * (benunit("benunit_universal_credit_reported", period) == 0)
            / 52
        )


class WTC_CTC_combined(Variable):
    value_type = float
    entity = BenUnit
    label = (
        u"Combined value of Working Tax Credit and Child Tax Credit per week"
    )
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("working_tax_credit", period) + benunit(
            "child_tax_credit", period
        )


class child_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Benefit amount received per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        num_children = benunit.nb_persons(BenUnit.CHILD)
        eldest_amount = (
            min_(num_children, 1)
            * parameters(period).benefits.child_benefit.amount_eldest
        )
        additional_amount = (
            max_(num_children - 1, 0)
            * parameters(period).benefits.child_benefit.amount_additional
        )
        return (eldest_amount + additional_amount) * (
            benunit("benunit_CB_reported", period) > 0
        )


class income_support_JSA_ib(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Support/JSA (income-based) amount received per week before eligibility is applied"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        younger_age = benunit("younger_adult_age", period)
        older_age = benunit("older_adult_age", period)
        personal_allowance = (
            benunit("is_single", period)
            * (
                (younger_age < 25)
                * parameters(period).benefits.income_support.amount_16_24
                + (younger_age >= 25)
                * parameters(period).benefits.income_support.amount_over_25
            )
            + benunit("is_couple", period)
            * (
                (younger_age < 18)
                * (older_age < 18)
                * parameters(
                    period
                ).benefits.income_support.amount_couples_16_17
                + (younger_age >= 18)
                * (older_age >= 18)
                * parameters(
                    period
                ).benefits.income_support.amount_couples_over_18
                + (younger_age < 18)
                * (younger_age >= 25)
                * parameters(
                    period
                ).benefits.income_support.amount_couples_age_gap
            )
            + benunit("is_lone_parent", period)
            * (
                (younger_age < 18)
                * parameters(period).benefits.income_support.amount_lone_16_17
                + (younger_age >= 18)
                * parameters(
                    period
                ).benefits.income_support.amount_lone_over_18
            )
        )
        has_carer = (
            benunit.max(benunit.members("carers_allowance_reported", period))
            > 0
        )
        has_disabled_adult = (
            benunit.sum(
                benunit.members("is_adult", period)
                * benunit.members("disabled", period)
            )
            > 0
        )
        premiums = (
            parameters(period).benefits.income_support.carer_premium
            * has_carer
            + parameters(period).benefits.income_support.disability_premium
            * has_disabled_adult
        )
        BENUNIT_MEANS_TESTED_BENEFITS = [
            "working_tax_credit",
            "child_tax_credit",
            "child_benefit",
        ]
        PERSON_MEANS_TESTED_BENEFITS = ["JSA_contrib"]
        benefits = sum(
            map(
                lambda benefit: benunit(benefit, period),
                BENUNIT_MEANS_TESTED_BENEFITS,
            )
        ) + sum(
            map(
                lambda benefit: benunit.sum(benunit.members(benefit, period)),
                PERSON_MEANS_TESTED_BENEFITS,
            )
        )
        means_tested_income = (
            benunit("benunit_post_tax_income", period) + benefits
        )
        income_deduction = max_(
            0,
            means_tested_income
            - benunit("is_single", period)
            * parameters(
                period
            ).benefits.income_support.income_disregard_single
            + benunit("is_couple", period)
            * parameters(
                period
            ).benefits.income_support.income_disregard_couple
            + benunit("is_lone_parent", period)
            * parameters(period).benefits.income_support.income_disregard_lone,
        )
        return max_(
            0,
            (personal_allowance + premiums - income_deduction),
        )


class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Support amount per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        already_claiming_IS = benunit("benunit_IS_reported", period) > 0
        not_claiming_JSA = benunit("benunit_JSA_income_reported", period) == 0
        eligible = already_claiming_IS * not_claiming_JSA
        return eligible * benunit("income_support_JSA_ib", period)


class JSA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"JSA (income-based) amount per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        already_claiming_JSA_IB = (
            benunit("benunit_JSA_income_reported", period) > 0
        )
        not_claiming_PC = (
            benunit("benunit_pension_credit_reported", period) == 0
        )
        not_claiming_IS = benunit("benunit_IS_reported", period) == 0
        eligible = already_claiming_JSA_IB * not_claiming_PC * not_claiming_IS
        return eligible * benunit("income_support_JSA_ib", period)


class pension_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"JSA (income-based) amount per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        already_claiming_PC = (
            benunit("benunit_pension_credit_reported", period) > 0
        )
        eligible = already_claiming_PC
        PC = benunit("pension_credit_GC", period) + benunit(
            "pension_credit_SC", period
        )
        return eligible * PC


class pension_credit_MG(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Minimum Guarantee) amount per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        PC_params = parameters(period).benefits.pension_credit
        personal_allowance = (
            benunit("is_single", period) * PC_params.minimum_guarantee_single
            + benunit("is_couple", period) * PC_params.minimum_guarantee_couple
        )
        eligible = (
            benunit.max(benunit.members("is_state_pension_age", period)) > 0
        )
        has_carer = (
            benunit.max(benunit.members("carers_allowance_reported", period))
            > 0
        )
        premiums = has_carer * PC_params.carer_premium
        applicable_amount = personal_allowance + premiums
        return applicable_amount * eligible


class pension_credit_GC(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Guarantee Credit) amount per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        means_tested_income = benunit("benunit_post_tax_income", period)
        return max_(
            0, benunit("pension_credit_MG", period) - means_tested_income
        )


class pension_credit_SC(Variable):
    value_type = float
    entity = BenUnit
    label = u"Pension Credit (Savings Credit) amount per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        PC_params = parameters(period).benefits.pension_credit
        income = benunit("benunit_post_tax_income", period)
        MG_amount = benunit("pension_credit_MG", period)
        threshold = PC_params.savings_credit_threshold_single * benunit(
            "is_single", period
        ) + PC_params.savings_credit_threshold_couple * benunit(
            "is_couple", period
        )
        maximum_amount = PC_params.savings_credit_max_single * benunit(
            "is_single", period
        ) + PC_params.savings_credit_max_couple * benunit("is_couple", period)
        income_above_threshold = max_(0, income - threshold)
        income_above_MG = max_(0, income - MG_amount)
        claiming_PC = benunit("benunit_pension_credit_reported", period) > 0
        SG_amount = min_(
            income_above_threshold
            * (1 - PC_params.savings_credit_reduction_rate),
            maximum_amount,
        )
        return max_(0, SG_amount * claiming_PC)


class benunit_housing_costs(Variable):
    value_type = float
    entity = BenUnit
    label = u"Housing costs per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("personal_housing_costs", period))


class housing_benefit_pre_means_test(Variable):
    value_type = float
    entity = BenUnit
    label = u"Housing Benefit per week, before means tests"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        HB_params = parameters(period).benefits.housing_benefit
        eligible_housing_costs = benunit.sum(
            benunit.members("personal_housing_costs", period)
        )
        num_children = benunit.sum(benunit.members("is_child", period))
        num_disabled_children = benunit.sum(
            benunit.members("disabled", period)
            * benunit.members("is_child", period)
        )
        is_pensioner_couple = benunit("is_couple", period) * (
            benunit.sum(benunit.members("is_state_pension_age", period)) > 0
        )
        is_single_pensioner = benunit("is_single", period) * (
            benunit.sum(benunit.members("is_state_pension_age", period)) > 0
        )
        applicable_amount = (
            HB_params.family_element
            + HB_params.child_premium * num_children
            + HB_params.disability_premium * num_disabled_children
            + HB_params.single_pensioner_premium * is_single_pensioner
            + HB_params.couple_pensioner_premium * is_pensioner_couple
        )
        return min_(applicable_amount, eligible_housing_costs)


class housing_benefit_post_means_test(Variable):
    value_type = float
    entity = BenUnit
    label = u"Housing Benefit per week, given eligibility"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        applicable_amount = benunit("housing_benefit_pre_means_test", period)
        eligible_housing_costs = benunit.sum(
            benunit.members("personal_housing_costs", period)
        )
        BENUNIT_MEANS_TESTED_BENEFITS = [
            "working_tax_credit",
            "child_tax_credit",
            "child_benefit",
        ]
        PERSON_MEANS_TESTED_BENEFITS = ["JSA_contrib"]
        benefits = sum(
            map(
                lambda benefit: benunit(benefit, period),
                BENUNIT_MEANS_TESTED_BENEFITS,
            )
        ) + sum(
            map(
                lambda benefit: benunit.sum(benunit.members(benefit, period)),
                PERSON_MEANS_TESTED_BENEFITS,
            )
        )
        hours_worked = benunit.sum(benunit.members("hours_worked", period))
        works_over_30_hours = (
            hours_worked
            >= parameters(
                period
            ).benefits.working_tax_credit.hours_requirement_single
        )
        means_tested_income = (
            benunit("benunit_post_tax_income", period) + benefits
        )
        income_deduction = max_(
            0,
            means_tested_income
            - benunit("is_single", period)
            * parameters(
                period
            ).benefits.income_support.income_disregard_single
            + benunit("is_couple", period)
            * parameters(
                period
            ).benefits.income_support.income_disregard_couple
            + benunit("is_lone_parent", period)
            * parameters(period).benefits.income_support.income_disregard_lone
            + works_over_30_hours
            * parameters(
                period
            ).benefits.housing_benefit.working_disregard_bonus,
        )
        reduction = max_(0, means_tested_income - applicable_amount) * 0.65
        receiving_IS_or_PC = (
            benunit("income_support", period)
            + benunit("pension_credit", period)
            + benunit("JSA_income", period)
            > 0
        )
        eligible_amount = (1 - receiving_IS_or_PC) * (
            eligible_housing_costs - reduction
        ) + receiving_IS_or_PC * eligible_housing_costs
        return max_(0, eligible_amount)


class housing_benefit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Housing Benefit amount per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return (
            benunit("housing_benefit_post_means_test", period)
            * (benunit("benunit_universal_credit_reported", period) == 0)
            * (benunit("benunit_housing_benefit_reported", period) > 0)
        )


class universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Universal Credit amount per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        UC_params = parameters(period).benefits.universal_credit
        is_single = benunit("is_single", period)
        is_couple = benunit("is_couple", period)
        is_over_25 = benunit("younger_adult_age", period) >= 25
        basic_amount = (
            is_single * (1 - is_over_25) * UC_params.basic_single_young
            + is_single * is_over_25 * UC_params.basic_single_older
            + is_couple * (1 - is_over_25) * UC_params.basic_couple_young
            + is_couple * is_over_25 * UC_params.basic_couple_older
        )
        has_carer = (
            benunit.max(benunit.members("carers_allowance_reported", period))
            > 0
        )
        num_eligible_children = min_(2, benunit.nb_persons(BenUnit.CHILD))
        num_eligible_disabled_children = benunit.sum(
            benunit.members("is_child", period)
            * benunit.members("disabled", period)
        )
        childcare_limit = (
            num_eligible_children == 1
        ) * UC_params.max_childcare_1 + (
            num_eligible_children > 1
        ) * UC_params.max_childcare_2
        is_disabled = benunit.sum(
            (1 - benunit.members("is_child", period))
            * benunit.members("disabled", period)
        )
        premiums = (
            has_carer * UC_params.carer_element
            + num_eligible_children * UC_params.child_element
            + num_eligible_disabled_children * UC_params.disabled_child_element
            + is_disabled * UC_params.disabled_element
        )
        eligible_childcare_costs = benunit.sum(
            benunit.members("eligible_childcare_cost", period)
        )
        childcare_element = min_(
            childcare_limit,
            eligible_childcare_costs * UC_params.childcare_cost_rate,
        )
        applicable_amount = (
            basic_amount
            + premiums
            + childcare_element
            + benunit("housing_benefit_pre_means_test", period)
        )
        earned_income = (
            benunit("benunit_earnings", period)
            + benunit.sum(benunit.members("taxed_means_tested_bonus", period))
            + benunit.sum(
                benunit.members("untaxed_means_tested_bonus", period)
            )
            - benunit("benunit_income_tax", period)
            - benunit("benunit_NI", period)
        )
        unearned_income = (
            benunit("benunit_pension_income", period)
            + benunit("benunit_state_pension", period)
            + benunit.sum(benunit.members("carers_allowance_reported", period))
            + benunit.sum(benunit.members("JSA_contrib", period))
        )
        earnings_reduction = max_(
            0, earned_income * 4 - UC_params.earn_disregard
        )
        final_amount = (
            max_(
                0,
                applicable_amount
                - unearned_income * 4
                - UC_params.reduction_rate * earnings_reduction,
            )
            / 4
        )
        already_claiming = (
            benunit("benunit_universal_credit_reported", period) > 0
        )
        return final_amount * already_claiming


class ESA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u'Amount of Employment and Support Allowance per week'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit("benunit_ESA_income_reported", period)
