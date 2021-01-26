from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit (reported amount)"
    definition_period = YEAR


class child_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit (reported amount)"
    definition_period = YEAR


class benunit_hours(Variable):
    value_type = float
    entity = BenUnit
    label = u"Total hours per week worked by the benefit unit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["weekly_hours"])


class is_CTC_child_limit_exempt(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the child was born before 2017 and therefore exempt from the two-child limit for Child Tax Credit"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (person("age", period.this_year) >= 3) * (
            1 - person("is_adult", period)
        )


class WTC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for WTC"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefits.working_tax_credit
        hours = benunit("benunit_hours", period)
        max_hours = benunit.max(benunit.members("weekly_hours", period))
        disabled_adults = benunit("disabled_adults", period)
        has_old = benunit.max(
            benunit.members("age", period.this_year) > WTC.min_hours.old_age
        )
        lower_req = (
            disabled_adults + has_old + benunit("is_lone_parent", period) > 0
        )
        medium_req = benunit("is_couple_parents", period) * (1 - lower_req)
        higher_req = (benunit("eldest_adult_age", period) >= 25) * (
            benunit("youngest_adult_age", period) < 60
        )
        meets_lower = hours >= WTC.min_hours.lower
        meets_medium = (hours >= WTC.min_hours.couple_with_children) * (
            max_hours >= WTC.min_hours.lower
        )
        meets_higher = hours >= WTC.min_hours.default
        eligible = (
            lower_req * meets_lower
            + medium_req * meets_medium
            + higher_req * meets_higher
        ) > 0
        return eligible


class CTC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for CTC"
    definition_period = YEAR

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
        return (
            children_eligible
            + benunit("disabled_children", period)
            + benunit("severely_disabled_children", period)
            > 0
        )


class WTC_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"WTC eligible amount"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefits.working_tax_credit
        applicable_amount = (
            WTC.elements.basic
            + benunit("is_couple", period) * WTC.elements.couple
            + (
                (
                    benunit.sum(
                        benunit.members("is_disabled", period)
                        * benunit.members("weekly_hours", period)
                    )
                    > WTC.min_hours.lower
                )
                > 0
            )
            * WTC.elements.disabled
            + benunit("severely_disabled_adults", period)
            * WTC.elements.severely_disabled
            + benunit("is_lone_parent", period) * WTC.elements.lone_parent
            + (benunit("benunit_hours", period) > WTC.min_hours.default)
            * WTC.elements.worker
        )
        num_children = benunit.nb_persons(BenUnit.CHILD)
        max_childcare_amount = (
            num_children == 1
        ) * WTC.elements.childcare_1 + (
            num_children > 1
        ) * WTC.elements.childcare_2
        childcare_element = min_(
            max_childcare_amount,
            WTC.elements.childcare_coverage
            * benunit.sum(
                benunit.members("childcare_cost", period.first_week)
            ),
        )
        return benunit("WTC_eligible", period) * (
            applicable_amount + childcare_element
        )


class CTC_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"CTC eligible amount"
    definition_period = YEAR

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
        CTC = parameters(period).benefits.child_tax_credit
        amount = (
            CTC.family_element
            + CTC.child_element * children_eligible
            + CTC.dis_child_element * benunit("disabled_children", period)
            + CTC.severe_dis_child_element
            * benunit("severely_disabled_children", period)
        )
        return benunit("CTC_eligible", period) * amount


class tax_credits_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reduction in tax credits from means-tested income"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        means_test = parameters(period).benefits.working_tax_credit.means_test
        child_tax_credit_amount = benunit("CTC_applicable_amount", period)
        working_tax_credit_amount = benunit("WTC_applicable_amount", period)
        CTC_only = (child_tax_credit_amount > 0) * (
            working_tax_credit_amount == 0
        )
        threshold = select(
            [CTC_only, not_(CTC_only)],
            [means_test.CTC_only_threshold, means_test.income_threshold],
        )
        means_tested_SSP = max_(
            0,
            benunit.sum(benunit.members("SSP", period))
            - means_test.SSP_disregard,
        )
        means_tested_earnings = (
            benunit("benunit_earnings", period)
        ) - benunit("benunit_pension_deductions", period)
        means_tested_SP = max_(
            0,
            benunit.sum(benunit.members("state_pension", period))
            + benunit.sum(benunit.members("pension_income", period))
            - means_test.pension_disregard,
        )
        means_tested_income = (
            means_tested_earnings + means_tested_SP + means_tested_SSP
        )
        reduction = (
            max_(0, (means_tested_income - threshold))
            * means_test.income_reduction_rate
        )
        return reduction


class yearly_working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Working Tax Credit received per week"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        amount = max_(
            0,
            benunit("WTC_applicable_amount", period)
            - benunit("tax_credits_reduction", period),
        )
        already_claiming = (
            benunit.sum(
                benunit.members(
                    "working_tax_credit_reported", period, options=[MATCH]
                )
            )
            > 0
        )
        return amount * already_claiming


class yearly_child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Amount of Child Tax Credit received per week"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reduction_left = max_(
            0,
            benunit("tax_credits_reduction", period)
            - benunit("WTC_applicable_amount", period),
        )
        amount = max_(
            0,
            benunit("CTC_applicable_amount", period) - reduction_left,
        )
        already_claiming = (
            benunit.sum(
                benunit.members(
                    "child_tax_credit_reported", period, options=[MATCH]
                )
            )
            > 0
        )
        return amount * already_claiming


class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Working Tax Credit"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit("yearly_working_tax_credit", period, options=[MATCH])


class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Working Tax Credit"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit("yearly_child_tax_credit", period, options=[MATCH])


class tax_credits(Variable):
    value_type = float
    entity = BenUnit
    label = u"Total Tax Credits receipt per week"
    definition_period = WEEK
    set_input = set_input_divide_by_period

    def formula(benunit, period, parameters):
        return benunit("working_tax_credit", period) + benunit(
            "child_tax_credit", period
        )
