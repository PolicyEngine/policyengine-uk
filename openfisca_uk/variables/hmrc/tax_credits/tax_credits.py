from openfisca_uk.model_api import *


class working_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Working Tax Credit"
    definition_period = YEAR
    unit = "currency-GBP"


class child_tax_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Working Tax Credit"
    definition_period = YEAR
    unit = "currency-GBP"


class tax_credits_applicable_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Applicable income for Tax Credits"
    definition_period = YEAR
    unit = "currency-GBP"
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
        return income * ~on_exempt_benefits


class is_CTC_child_limit_exempt(Variable):
    value_type = bool
    entity = Person
    label = "Exemption from Child Tax Credit child limit"
    documentation = "Exemption from Child Tax Credit limit on number of children based on birth year"
    definition_period = YEAR

    def formula(person, period, parameters):
        limit_year = parameters(
            period
        ).benefit.tax_credits.child_tax_credit.limit.start_year
        # Children must be born before April 2017.
        # We use < 2017 as the closer approximation than <= 2017.
        return person("birth_year", period) < limit_year


class is_child_for_CTC(Variable):
    value_type = bool
    entity = Person
    label = "Child eligible for Child Tax Credit"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 8"

    def formula(person, period, parameters):
        return person("is_child_or_QYP", period)


class is_CTC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Child Tax Credit eligibility"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 8"

    def formula(benunit, period, parameters):
        return benunit.any(benunit.members("is_child_for_CTC", period))


class would_claim_CTC(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Child Tax Credit"
    documentation = (
        "Whether this family would claim Child Tax Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        takes_up = (
            random(benunit)
            <= parameters(period).benefit.tax_credits.child_tax_credit.takeup
        )
        return takes_up | benunit("claims_all_entitled_benefits", period)


class claims_CTC(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this family is imputed to claim Child Tax Credit, based on survey response and take-up rates"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        would_claim_CTC = benunit("would_claim_CTC", period)
        claims_legacy_benefits = benunit("claims_legacy_benefits", period)
        return would_claim_CTC & claims_legacy_benefits


class CTC_maximum_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Maximum Child Tax Credit"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = "currency-GBP"

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
    label = "CTC entitlement in the Family Element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = "currency-GBP"

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
    label = "Child Tax Credit child element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        person = benunit.members
        CTC = parameters(period).benefit.tax_credits.child_tax_credit
        is_child_for_CTC = person("is_child_for_CTC", period)
        is_CTC_child_limit_exempt = person("is_CTC_child_limit_exempt", period)
        exempt_child = is_child_for_CTC & is_CTC_child_limit_exempt
        exempt_children = benunit.sum(exempt_child)
        child_limit = CTC.limit.child_count
        spaces_left = max_(0, child_limit - exempt_children)
        non_exempt_children = min_(spaces_left, benunit.sum(is_child_for_CTC))
        children = exempt_children + non_exempt_children
        amount = CTC.elements.child_element * children
        return amount * benunit("claims_CTC", period)


class CTC_disabled_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = "CTC entitlement from disabled child elements"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        person = benunit.members
        is_child_for_CTC = person("is_child_for_CTC", period)
        is_disabled_for_benefits = person("is_disabled_for_benefits", period)
        is_disabled_child = is_child_for_CTC & is_disabled_for_benefits
        disabled_children = benunit.sum(is_disabled_child)
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
    label = "CTC entitlement from severely disabled child elements"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 9"
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        person = benunit.members
        is_child_for_CTC = person("is_child_for_CTC", period)
        is_severely_disabled_for_benefits = person(
            "is_severely_disabled_for_benefits", period
        )
        is_severely_disabled_child = (
            is_child_for_CTC & is_severely_disabled_for_benefits
        )
        severely_disabled_children = benunit.sum(is_severely_disabled_child)
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
    label = "Working Tax Credit eligibility"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 10"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        person = benunit.members
        person_hours = person("weekly_hours", period)
        total_hours = benunit.sum(person_hours)
        max_person_hours = benunit.max(person_hours)
        has_disabled_adults = benunit("num_disabled_adults", period) > 0
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        old = person("age", period.this_year) >= WTC.min_hours.old_age
        has_old = benunit.any(old)
        lone_parent = family_type == families.LONE_PARENT
        couple_with_children = family_type == families.COUPLE_WITH_CHILDREN
        eldest_25_plus = benunit("eldest_adult_age", period) >= 25
        youngest_under_60 = benunit("youngest_adult_age", period) < 60
        # Calculate WTC eligibility group.
        lower_req = has_disabled_adults | has_old | lone_parent
        medium_req = couple_with_children & ~lower_req
        higher_req = eldest_25_plus & youngest_under_60
        # Calculate eligibility for each WTC group.
        meets_lower = total_hours >= WTC.min_hours.lower
        meets_medium_total_hours = (
            total_hours >= WTC.min_hours.couple_with_children
        )
        meets_medium_person_hours = max_person_hours >= WTC.min_hours.lower
        meets_medium = meets_medium_total_hours & meets_medium_person_hours
        meets_higher = total_hours >= WTC.min_hours.default
        return (
            (lower_req & meets_lower)
            | (medium_req & meets_medium)
            | (higher_req & meets_higher)
        )


class would_claim_WTC(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Working Tax Credit"
    documentation = (
        "Whether this family would claim Working Tax Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        takeup_rate = parameters(
            period
        ).benefit.tax_credits.working_tax_credit.takeup
        takes_up = random(benunit) < takeup_rate
        would_take_up = benunit("claims_legacy_benefits", period) & takes_up
        return would_take_up | benunit("claims_all_entitled_benefits", period)


class claims_WTC(Variable):
    value_type = bool
    entity = BenUnit
    label = "Whether this family is imputed to claim Working Tax Credit, based on survey response and take-up rates"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        would_claim_WTC = benunit("would_claim_WTC", period)
        claims_legacy_benefits = benunit("claims_legacy_benefits", period)
        return would_claim_WTC & claims_legacy_benefits


class WTC_maximum_rate(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit maximum rate"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = "currency-GBP"

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
    label = "Working Tax Credit basic element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = "currency-GBP"

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
    label = "Working Tax Credit couple element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = "currency-GBP"

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
    label = "Working Tax Credit lone parent element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        family_type = benunit("family_type", period)
        families = family_type.possible_values
        lone_parent = family_type == families.LONE_PARENT
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * lone_parent
            * WTC.elements.lone_parent
        )


class WTC_disabled_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit disabled element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        person = benunit.members
        person_meets_hours = (
            person("weekly_hours", period) >= WTC.min_hours.lower
        )
        person_qualifies = (
            person_meets_hours
            & person("is_disabled_for_benefits", period)
            & person("is_adult", period)
        )
        qualifies = benunit.any(person_qualifies)
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * qualifies
            * WTC.elements.disabled
        )


class WTC_severely_disabled_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit severely disabled element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = "currency-GBP"

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
    label = "Working Tax Credit worker element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        hours = aggr(benunit, period, ["weekly_hours"])
        meets_hours_requirement = hours >= WTC.min_hours.default
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * meets_hours_requirement
            * WTC.elements.worker
        )


class WTC_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit childcare element"
    definition_period = YEAR
    reference = "Tax Credits Act 2002 s. 11"
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        WTC = parameters(period).benefit.tax_credits.working_tax_credit
        num_children = benunit("num_children", period)
        childcare_1 = (num_children == 1) * WTC.elements.childcare_1
        childcare_2 = (num_children > 1) * WTC.elements.childcare_2
        max_childcare_amount = (childcare_1 + childcare_2) * WEEKS_IN_YEAR
        expenses = aggr(benunit, period, ["childcare_expenses"])
        eligible_expenses = min_(max_childcare_amount, expenses)
        childcare_element = WTC.elements.childcare_coverage * eligible_expenses
        return (
            benunit("is_WTC_eligible", period)
            * benunit("claims_WTC", period)
            * childcare_element
        )


class tax_credits_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Reduction in Tax Credits from means-tested income"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        means_test = parameters(period).benefit.tax_credits.means_test
        CTC_amount = benunit("CTC_maximum_rate", period)
        WTC_amount = benunit("WTC_maximum_rate", period)
        CTC_only = (CTC_amount > 0) & (WTC_amount == 0)
        threshold = where(
            CTC_only,
            means_test.income_threshold_CTC_only,
            means_test.income_threshold,
        )
        income = benunit("tax_credits_applicable_income", period)
        overage = max_(0, income - threshold)
        return overage * means_test.income_reduction_rate


class working_tax_credit_pre_minimum(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit pre-minimum"
    documentation = (
        "Working Tax Credit amount before the minimum tax credit is applied"
    )
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return max_(
            0,
            benunit("WTC_maximum_rate", period)
            - benunit("tax_credits_reduction", period),
        )


class child_tax_credit_pre_minimum(Variable):
    value_type = float
    entity = BenUnit
    label = "Child Tax Credit pre-minimum"
    documentation = (
        "Child Tax Credit amount before the minimum tax credit is applied"
    )
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        reduction_left = max_(
            0,
            benunit("tax_credits_reduction", period)
            - benunit("WTC_maximum_rate", period),
        )
        return max_(
            0,
            benunit("CTC_maximum_rate", period) - reduction_left,
        )


class tax_credits(Variable):
    value_type = float
    entity = BenUnit
    label = "Tax Credits"
    documentation = "Value of the Tax Credits (benefits) for this family"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        amount = add(
            person,
            period,
            ["working_tax_credit_pre_minimum", "child_tax_credit_pre_minimum"],
        )
        min_benefit = parameters(period).benefit.tax_credits.min_benefit
        return where(amount < min_benefit, 0, amount)


class child_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Child Tax Credit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return where(
            benunit("tax_credits", period) > 0,
            benunit("child_tax_credit_pre_minimum", period),
            0,
        )


class working_tax_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Working Tax Credit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return where(
            benunit("tax_credits", period) > 0,
            benunit("working_tax_credit_pre_minimum", period),
            0,
        )
