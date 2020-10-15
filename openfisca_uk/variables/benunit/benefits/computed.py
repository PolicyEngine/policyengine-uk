from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np

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
        return eldest_amount + additional_amount

class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = u'Income Support amount received per week'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("income_support_reported", period))

class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u'Child Tax Credit amount received per week'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("child_tax_credit_reported", period))

class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u'Child Tax Credit amount received per week'
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("working_tax_credit_reported", period))

'''

class income_support(Variable):
    value_type = float
    entity = BenUnit
    label = u"Income Support amount received per week"
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
        means_tested_income = benunit(
            "benunit_post_tax_income", period
        ) + benunit.sum(benunit.members("JSA_contrib_reported", period))
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
        has_children = benunit.nb_persons(BenUnit.CHILD) > 0
        random = np.random.rand(*has_children.shape)
        takeup = (random < 0.89) * has_children + (random < 0.82) * (
            1 - has_children
        )
        return max_(
            0,
            (personal_allowance - income_deduction)
            * (
                benunit.sum(
                    benunit.members("income_support_reported", period) > 0
                )
            )
            * takeup,
        )





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
        yearly_amount = (
            parameters(period).benefits.child_tax_credit.family_element
            + parameters(period).benefits.child_tax_credit.child_element
            * children_eligible
        )
        return yearly_amount * (children_eligible > 0)


class child_working_tax_credit_reduction(Variable):
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
        threshold = (
            eligible_for_both
            * parameters(period).benefits.working_tax_credit.income_threshold
            + (child_tax_credit_amount > 0)
            * (1 - eligible_for_both)
            * parameters(period).benefits.child_tax_credit.income_threshold
        )
        reduction = (
            max_(0, (benunit("benunit_income", period) * 52 - threshold))
            * parameters(
                period
            ).benefits.child_tax_credit.income_reduction_rate
        )
        return reduction


class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Working Tax Credit received per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        single = benunit("is_single", period)
        couple = benunit("is_couple", period)
        random = np.random.rand(*single.shape)
        no_CTC = benunit("child_tax_credit", period) == 0
        takeup = (
            (random < 0.35) * single * no_CTC
            + (random < 0.23) * couple * no_CTC
            + (random < 0.84) * (1 - no_CTC)
        )
        return (
            takeup
            * max_(
                0,
                benunit("working_tax_credit_pre_means_test", period)
                - benunit("child_working_tax_credit_reduction", period),
            )
            / 52
        )


class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Working Tax Credit received per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        random = np.random.rand(*benunit("is_single", period).shape)
        takeup = random < 0.84
        reduction_left = takeup * min_(
            0,
            benunit("working_tax_credit_pre_means_test", period)
            - benunit("child_working_tax_credit_reduction", period),
        )
        return (
            max_(
                0,
                benunit("child_tax_credit_pre_means_test", period)
                + reduction_left,
            )
            / 52
        )


class working_tax_credit_pre_means_test(Variable):
    value_type = float
    entity = BenUnit
    label = (
        u"Working Tax Credit amount received per year, before means testing"
    )
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        hours_worked = benunit.sum(benunit.members("hours_worked", period))
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
            + benunit("is_lone_parent", period)
            * (
                hours_worked
                >= parameters(
                    period
                ).benefits.working_tax_credit.hours_requirement_lone_parent
            )
        )
        amount = (
            parameters(period).benefits.working_tax_credit.amount_basic
            + (
                hours_worked
                >= parameters(
                    period
                ).benefits.working_tax_credit.hours_requirement_single
            )
            * parameters(period).benefits.working_tax_credit.amount_worker
            + benunit("is_couple", period)
            * parameters(period).benefits.working_tax_credit.amount_couple
            + benunit("is_lone_parent", period)
            * parameters(period).benefits.working_tax_credit.amount_lone_parent
        )
        return amount * eligible


class JSA_contrib(Variable):
    value_type = float
    entity = BenUnit
    label = u"JSA (contributory) amount received per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        age = benunit("younger_adult_age", period)
        is_couple = benunit.nb_persons(BenUnit.ADULT) == 2
        single_young = (age >= 18) * (age < 25) * (np.logical_not(is_couple))
        single_old = (age >= 25) * (np.logical_not(is_couple))
        personal_allowance = (
            single_young * parameters(period).benefits.JSA.contrib.amount_18_24
            + single_old
            * parameters(period).benefits.JSA.contrib.amount_over_25
            + is_couple * parameters(period).benefits.JSA.contrib.amount_couple
        )
        earnings_deduction = max_(
            0,
            benunit("benunit_earnings", period)
            - parameters(period).benefits.JSA.contrib.earn_disregard,
        )
        pension_deduction = max_(
            0,
            benunit("benunit_pension_income", period)
            - parameters(period).benefits.JSA.contrib.pension_disregard,
        )
        return max_(
            0,
            (personal_allowance - earnings_deduction - pension_deduction)
            * (
                benunit.sum(benunit.members("JSA_contrib_reported", period))
                > 0
            ),
        )


class JSA_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"JSA (income-based) amount received per week"
    definition_period = ETERNITY

    def formula(benunit, period, parameters):
        younger_age = benunit("younger_adult_age", period)
        older_age = benunit("older_adult_age", period)
        personal_allowance = (
            benunit("is_single", period)
            * (
                (younger_age < 25)
                * parameters(period).benefits.JSA.income.amount_16_24
                + (younger_age >= 25)
                * parameters(period).benefits.JSA.income.amount_over_25
            )
            + benunit("is_couple", period)
            * (
                (younger_age < 18)
                * (older_age < 18)
                * parameters(period).benefits.JSA.income.amount_couples_16_17
                + (younger_age >= 18)
                * (older_age >= 18)
                * parameters(period).benefits.JSA.income.amount_couples_over_18
                + (younger_age < 18)
                * (younger_age >= 25)
                * parameters(period).benefits.JSA.income.amount_couples_age_gap
            )
            + benunit("is_lone_parent", period)
            * (
                (younger_age < 18)
                * parameters(period).benefits.JSA.income.amount_lone_16_17
                + (younger_age >= 18)
                * parameters(period).benefits.JSA.income.amount_lone_over_18
            )
        )
        means_tested_income = benunit(
            "benunit_post_tax_income", period
        ) + benunit("JSA_contrib", period)
        income_deduction = max_(
            0,
            means_tested_income
            - benunit("is_single", period)
            * parameters(period).benefits.JSA.income.income_disregard_single
            + benunit("is_couple", period)
            * parameters(period).benefits.JSA.income.income_disregard_couple
            + benunit("is_lone_parent", period)
            * parameters(period).benefits.JSA.income.income_disregard_lone,
        )
        return benunit("looking_for_work", period) * max_(
            0, (personal_allowance - income_deduction)
        )

'''