from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit"
    definition_period = YEAR


class child_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Working Tax Credit"
    definition_period = YEAR


class tax_credits_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"Applicable income for Tax Credits"
    definition_period = YEAR
    reference = "The Tax Credits (Definition and Calculation of Income) Regulations 2002 s. 3"

    def formula(benunit, period, parameters):
        TC = parameters(period).benefit.tax_credits
        STEP_1_COMPONENTS = [
            "pension_income",
            "savings_interest_income",
            "dividend_income",
            "property_income",
        ]
        income = aggr(benunit, period, STEP_1_COMPONENTS)
        income = amount_over(income, TC.means_test.non_earned_disregard)
        STEP_2_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "social_security_income",
            "miscellaneous_income",
        ]
        income += aggr(benunit, period, STEP_2_COMPONENTS)
        EXEMPT_BENEFITS = ["income_support", "ESA_income", "JSA_income"]
        on_exempt_benefits = add(benunit, period, EXEMPT_BENEFITS) > 0
        return income * not_(on_exempt_benefits)


class is_CTC_child_limit_exempt(Variable):
    value_type = bool
    entity = Person
    label = u"Whether the person was born before 2017 and therefore exempt from the two-child limit for Child Tax Credit"
    definition_period = YEAR

    def formula(person, period, parameters):
        limit_year = parameters(
            period
        ).benefit.tax_credits.child_tax_credit.two_child_limit_year
        born_after = person("birth_year", period.this_year) <= limit_year
        return born_after


class is_child_for_CTC(Variable):
    value_type = bool
    entity = Person
    label = u"Whether this person is a child conferring CTC eligibility"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 8"

    def formula(person, period, parameters):
        return person("is_child_or_QYP", period)


class is_CTC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the family is eligible for CTC"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 8"

    def formula(benunit, period, parameters):
        return benunit.sum(benunit.members("is_child_for_CTC", period)) >= 1


class would_claim_CTC(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Would claim Child Tax Credit"
    documentation = (
        "Whether this family would claim Child Tax Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return (
            random(benunit)
            <= parameters(period).benefit.tax_credits.child_tax_credit.takeup
        ) + benunit("claims_all_entitled_benefits", period)


class claims_CTC(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether this family is imputed to claim Child Tax Credit, based on survey response and take-up rates"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("would_claim_CTC", period) & benunit(
            "claims_legacy_benefits", period
        )


class CTC_maximum_rate(Variable):
    value_type = float
    entity = BenUnit
    label = u"The maximum rate of CTC"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"

    def formula(benunit, period, parameters):
        ELEMENTS = [
            "CTC_family_element",
            "CTC_child_element",
            "CTC_disabled_child_element",
            "CTC_severely_disabled_child_element",
        ]
        return add(benunit, period, ELEMENTS)


class CTC_family_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"CTC entitlement in the Family Element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"

    def formula(benunit, period, parameters):
        CTC = parameters(period).benefit.tax_credits.child_tax_credit
        return (
            benunit("is_CTC_eligible", period)
            * benunit("claims_CTC", period)
            * CTC.elements.family_element
        )


class CTC_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"CTC entitlement from child elements"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"

    def formula(benunit, period, parameters):
        exempt_children = benunit.sum(
            benunit.members("is_child_for_CTC", period)
            * benunit.members("is_CTC_child_limit_exempt", period)
        )
        spaces_left = max_(0, 2 - exempt_children)
        non_exempt_children = min_(
            spaces_left,
            benunit.sum(benunit.members("is_child_for_CTC", period)),
        )
        children = exempt_children + non_exempt_children
        CTC = parameters(period).benefit.tax_credits.child_tax_credit
        amount = CTC.elements.child_element * children
        return amount * benunit("claims_CTC", period)


class CTC_disabled_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"CTC entitlement from disabled child elements"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"

    def formula(benunit, period, parameters):
        disabled_children = benunit.sum(
            benunit.members("is_child_for_CTC", period)
            * (benunit.members("is_disabled_for_benefits", period))
            > 0
        )
        CTC = parameters(period).benefit.tax_credits.child_tax_credit
        amount = CTC.elements.dis_child_element * disabled_children
        return (
            benunit("is_CTC_eligible", period)
            * benunit("claims_CTC", period)
            * amount
        )


class CTC_severely_disabled_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"CTC entitlement from severely disabled child elements"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"

    def formula(benunit, period, parameters):
        severely_disabled_children = benunit.sum(
            benunit.members("is_child_for_CTC", period)
            * (
                benunit.members("is_severely_disabled_for_benefits", period)
                > 0
            )
        )
        CTC = parameters(period).benefit.tax_credits.child_tax_credit
        amount = (
            CTC.elements.severe_dis_child_element * severely_disabled_children
        )
        return (
            benunit("is_CTC_eligible", period)
            * benunit("claims_CTC", period)
            * amount
        )


class is_WTC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether the family is eligible for WTC"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 10"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        person_hours = benunit.members("weekly_hours", period)
        hours = benunit.sum(person_hours)
        max_hours = benunit.max(person_hours)
        disabled_adults = benunit("num_disabled_adults", period)
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        has_old = benunit.max(
            benunit.members("age", period.this_year) > WTC.min_hours.old_age
        )
        lower_req = (
            disabled_adults + has_old + (family_type == families.LONE_PARENT)
            > 0
        )
        medium_req = (family_type == families.COUPLE_WITH_CHILDREN) * (
            1 - lower_req
        ) > 0
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


class would_claim_WTC(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Would claim Working Tax Credit"
    documentation = (
        "Whether this family would claim Working Tax Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        takeup_rate = parameters(
            period
        ).benefit.tax_credits.working_tax_credit.takeup
        return benunit("claims_legacy_benefits", period) & (
            random(benunit) < takeup_rate
        ) | benunit("claims_all_entitled_benefits", period)


class claims_WTC(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether this family is imputed to claim Working Tax Credit, based on survey response and take-up rates"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit("would_claim_WTC", period) & benunit(
            "claims_legacy_benefits", period
        )


class WTC_maximum_rate(Variable):
    value_type = float
    entity = BenUnit
    label = u"The maximum rate of WTC"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"

    def formula(benunit, period, parameters):
        ELEMENTS = [
            "WTC_basic_element",
            "WTC_couple_element",
            "WTC_lone_parent_element",
            "WTC_disabled_element",
            "WTC_severely_disabled_element",
            "WTC_worker_element",
            "WTC_childcare_element",
        ]
        return add(benunit, period, ELEMENTS)


class WTC_basic_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"WTC entitlement from the basic element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * WTC.elements.basic
        )


class WTC_couple_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"WTC entitlement from the couple element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        relation_type = benunit("relation_type", period)
        relations = relation_type.possible_values
        amount = (relation_type == relations.COUPLE) * WTC.elements.couple
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * amount
        )


class WTC_lone_parent_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"WTC entitlement from the lone parent element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        amount = (
            family_type == families.LONE_PARENT
        ) * WTC.elements.lone_parent
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * amount
        )


class WTC_disabled_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"WTC entitlement from the disabled element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        condition = (
            benunit.sum(
                (benunit.members("is_disabled_for_benefits", period) > 0)
                * benunit.members("is_adult", period)
                * benunit.members("weekly_hours", period)
            )
            > WTC.min_hours.lower
        ) > 0
        amount = condition * WTC.elements.disabled
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * amount
        )


class WTC_severely_disabled_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"WTC entitlement from the severely disabled element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        amount = (
            benunit("num_severely_disabled_adults", period)
            * WTC.elements.severely_disabled
        )
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * amount
        )


class WTC_worker_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"WTC entitlement from the worker element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        hours = benunit.sum(benunit.members("weekly_hours", period))
        amount = (hours > WTC.min_hours.default) * WTC.elements.worker
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * amount
        )


class WTC_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"WTC entitlement from the childcare element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        num_children = benunit("num_children", period)
        max_childcare_amount = (
            num_children == 1
        ) * WTC.elements.childcare_1 * WEEKS_IN_YEAR + (
            num_children > 1
        ) * WTC.elements.childcare_2 * WEEKS_IN_YEAR
        childcare_element = min_(
            max_childcare_amount,
            WTC.elements.childcare_coverage
            * benunit.sum(benunit.members("childcare_expenses", period)),
        )
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * childcare_element
        )


class tax_credits_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reduction in Tax Credits from means-tested income"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        means_test = parameters(period).benefit.tax_credits.means_test
        child_tax_credit_amount = benunit("CTC_maximum_rate", period)
        working_tax_credit_amount = benunit("WTC_maximum_rate", period)
        CTC_only = (child_tax_credit_amount > 0) * (
            working_tax_credit_amount == 0
        )
        threshold = select(
            [CTC_only, not_(CTC_only)],
            [
                means_test.income_threshold_CTC_only,
                means_test.income_threshold,
            ],
        )
        income = benunit("tax_credits_applicable_income", period)
        reduction = (
            max_(0, (income - threshold)) * means_test.income_reduction_rate
        )
        return reduction


class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Working Tax Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        amount = max_(
            0,
            benunit("WTC_maximum_rate", period)
            - benunit("tax_credits_reduction", period),
        )
        return amount


class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Child Tax Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        reduction_left = max_(
            0,
            benunit("tax_credits_reduction", period)
            - benunit("WTC_maximum_rate", period),
        )
        amount = max_(
            0,
            benunit("CTC_maximum_rate", period) - reduction_left,
        )
        return amount


class tax_credits(Variable):
    value_type = float
    entity = BenUnit
    label = u"Value of the Tax Credits (benefits) for this family"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("working_tax_credit", period) + person(
            "child_tax_credit", period
        )
