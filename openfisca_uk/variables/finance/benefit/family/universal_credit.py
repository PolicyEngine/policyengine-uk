from openfisca_uk.tools.general import *
from openfisca_uk.entities import *
from openfisca_uk.variables.demographic.household import TenureType


class claims_UC(Variable):
    value_type = bool
    entity = BenUnit
    label = "Claims UC"
    documentation = (
        "Whether this family would claim Universal Credit if eligible"
    )
    definition_period = YEAR
    metadata = dict(
        policyengine=dict(
            type="bool",
            default=True,
        )
    )

    def formula(benunit, period, parameters):
        WTC = benunit("would_claim_WTC", period) & benunit(
            "is_WTC_eligible", period
        )
        CTC = benunit("would_claim_CTC", period) & benunit(
            "is_CTC_eligible", period
        )
        HB = benunit("would_claim_HB", period) & benunit(
            "housing_benefit_eligible", period
        )
        IS = benunit("would_claim_IS", period) & benunit(
            "income_support_eligible", period
        )
        ESA_income = benunit("would_claim_ESA_income", period) & benunit(
            "ESA_income_eligible", period
        )
        JSA_income = benunit("would_claim_JSA", period) & benunit(
            "JSA_income_eligible", period
        )
        return not_(benunit("claims_legacy_benefits", period)) & (
            sum([WTC, CTC, HB, IS, ESA_income, JSA_income]) > 0
        )


class is_UC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Universal Credit eligible"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.max(benunit.members("is_WA_adult", period)) > 0


class universal_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Universal Credit"
    definition_period = YEAR


class UC_maximum_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"Maximum UC amount"
    definition_period = YEAR

    def formula(benunit, period):
        return add(
            benunit,
            period,
            [
                "UC_standard_allowance",
                "UC_child_element",
                "UC_disability_element",
                "UC_carer_element",
                "UC_housing_costs_element",
                "UC_childcare_element",
            ],
        )


class UCClaimantType(Enum):
    SINGLE_YOUNG = "Single, under 25"
    SINGLE_OLD = "Single, 25 or over"
    COUPLE_YOUNG = "Couple, both under 25"
    COUPLE_OLD = "Couple, one over 25"


class UC_claimant_type(Variable):
    value_type = Enum
    possible_values = UCClaimantType
    default_value = UCClaimantType.SINGLE_YOUNG
    entity = BenUnit
    label = u"UC claimant type"
    definition_period = YEAR

    def formula(benunit, period):
        is_single = benunit("is_single", period)
        one_over_25 = benunit("eldest_adult_age", period.this_year) >= 25
        return select(
            [
                is_single * not_(one_over_25),
                is_single * one_over_25,
                not_(is_single) * not_(one_over_25),
                not_(is_single) * one_over_25,
            ],
            [
                UCClaimantType.SINGLE_YOUNG,
                UCClaimantType.SINGLE_OLD,
                UCClaimantType.COUPLE_YOUNG,
                UCClaimantType.COUPLE_OLD,
            ],
        )


class UC_standard_allowance(Variable):
    value_type = float
    entity = BenUnit
    label = u"UC Standard Allowance"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        SA = parameters(period).benefit.universal_credit.standard_allowance
        basic_amount = (
            SA.amount[benunit("UC_claimant_type", period)] * MONTHS_IN_YEAR
        )
        return basic_amount


class is_child_born_before_child_limit(Variable):
    value_type = bool
    entity = Person
    label = u"Born before child limit (exempt)"
    definition_period = YEAR

    def formula(person, period, parameters):
        UC = parameters(period).benefit.universal_credit
        start_year = UC.elements.child.limit.start_year
        born_before_limit = person("birth_year", period) < start_year
        return person("is_child", period) * born_before_limit


class UC_individual_child_element(Variable):
    value_type = float
    entity = Person
    label = u"UC child element for the child"
    definition_period = YEAR

    def formula(person, period, parameters):
        child_index = person("child_index", period)
        born_before_limit = person("is_child_born_before_child_limit", period)
        is_eligible = child_index <= person.benunit(
            "num_UC_eligible_children", period
        )
        UC = parameters(period).benefit.universal_credit
        return (
            select(
                [
                    (child_index == 1) & born_before_limit,
                    child_index == 1,
                    (child_index > 1) & is_eligible,
                    True,
                ],
                [
                    UC.elements.child.first.higher_amount,
                    UC.elements.child.amount,
                    UC.elements.child.amount,
                    0,
                ],
            )
            * MONTHS_IN_YEAR
        )


class num_UC_eligible_children(Variable):
    value_type = int
    entity = BenUnit
    label = u"Eligible children"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        children_born_before_limit = benunit.sum(
            benunit.members("is_child_born_before_child_limit", period)
        )
        child_limit = parameters(
            period
        ).benefit.universal_credit.elements.child.limit.num_children
        spaces_left = clip(
            child_limit - children_born_before_limit, 0, child_limit
        )
        spaces_filled = min_(
            spaces_left,
            benunit("num_children", period) - children_born_before_limit,
        )
        return children_born_before_limit + spaces_filled


class UC_child_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"UC child element"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        return benunit.sum(
            benunit.members("UC_individual_child_element", period)
        )


class UC_carer_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"UC carer element"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        has_carer = (
            aggr(benunit, period.this_year, ["is_carer_for_benefits"]) > 0
        )
        return UC.elements.carer.amount * has_carer * MONTHS_IN_YEAR


class UC_housing_costs_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"UC housing costs element"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        tenure_type = benunit.value_from_first_person(
            benunit.members.household("tenure_type", period).decode_to_str()
        )
        rent = benunit("benunit_rent", period)
        max_housing_costs = select(
            [
                (tenure_type == TenureType.RENT_FROM_COUNCIL.name)
                | (tenure_type == TenureType.RENT_FROM_HA.name),
                tenure_type == TenureType.RENT_PRIVATELY.name,
                True,
            ],
            [
                rent,
                min_(benunit("LHA_cap", period), rent),
                0,
            ],
        )
        return max_housing_costs - benunit("UC_non_dep_deductions", period)


class UC_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = u"Non-dependent deduction (individual)"
    definition_period = YEAR

    def formula(person, period, parameters):
        not_rent_liable = person.benunit("benunit_rent", period) == 0
        over_21 = person("age", period) >= 21
        deduction = parameters(
            period
        ).benefit.universal_credit.elements.housing.non_dep_deduction
        return deduction * over_21 * not_rent_liable * MONTHS_IN_YEAR


class UC_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = u"Non-dependent deductions"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        # Deductions are made for non-dependents outside the benefit unit,
        # but within the household, who meet certain conditions. To do this,
        # we first calculate the non-dependent deduction for each person (from
        # the perspective of a different benefit unit). Then, to calculate
        # the deduction for non-dependents outside the benefit unit, we subtract
        # the total non-dependent deductions for the benefit unit members from
        # the deductions for household members.
        non_dep_deductions_in_hh = benunit.max(
            benunit.members.household.sum(
                benunit.members("UC_individual_non_dep_deduction", period)
            )
        )
        non_dep_deductions_in_bu = benunit.sum(
            benunit.members("UC_individual_non_dep_deduction", period)
        )
        return non_dep_deductions_in_hh - non_dep_deductions_in_bu


class UC_individual_disabled_element(Variable):
    value_type = float
    entity = Person
    label = u"Disabled element of UC"
    definition_period = YEAR

    def formula(person, period, parameters):
        UC = parameters(period).benefit.universal_credit
        return person("is_disabled_for_benefits", period) * where(
            person("is_child", period),
            UC.elements.child.disabled.amount,
            UC.elements.disabled.amount,
        )


class UC_individual_severely_disabled_element(Variable):
    value_type = float
    entity = Person
    label = u"Severely disabled element of UC"
    documentation = u"Stacks with the disabled element"
    definition_period = YEAR

    def formula(person, period, parameters):
        UC = parameters(period).benefit.universal_credit
        return (
            person("is_severely_disabled_for_benefits", period)
            * person("is_child", period)
            * UC.elements.child.severely_disabled.amount
        )


class UC_disability_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"UC disability element"
    definition_period = YEAR

    def formula(benunit, period):
        return aggr(
            benunit,
            period,
            [
                "UC_individual_disabled_element",
                "UC_individual_severely_disabled_element",
            ],
        )


class UC_childcare_work_condition(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Meets childcare work condition"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/32/2020-04-06"
    )

    def formula(benunit, period, parameters):
        adults_not_in_work = benunit.members("is_adult", period) * not_(
            benunit.members("in_work", period)
        )
        return not_(benunit.any(adults_not_in_work))


class UC_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = u"UC childcare element"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        eligible_childcare_expenses = benunit.sum(
            benunit.members("childcare_expenses", period)
        )
        children = benunit("num_UC_eligible_children", period)
        childcare_limit = (
            UC.elements.childcare.maximum[clip(children, 1, 2)]
            * MONTHS_IN_YEAR
        )
        childcare_element = min_(
            childcare_limit,
            eligible_childcare_expenses * UC.elements.childcare.coverage_rate,
        )
        return (
            benunit("UC_childcare_work_condition", period) * childcare_element
        )


class UC_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"UC earned income (after disregards)"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "miscellaneous_income",
            "self_employment_income",
        ]
        earned_income = aggr(benunit, period, INCOME_COMPONENTS)
        earned_income = max_(
            0,
            earned_income
            - aggr(
                benunit,
                period,
                ["income_tax", "national_insurance"],
            ),
        )
        housing = benunit("UC_housing_costs_element", period)
        earnings_disregard = (
            where(
                housing == 0,
                UC.means_test.earn_disregard,
                UC.means_test.earn_disregard_with_housing,
            )
            * MONTHS_IN_YEAR
        )
        return max_(0, earned_income - earnings_disregard)


class UC_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = u"UC unearned income"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return aggr(
            benunit,
            period,
            [
                "carers_allowance",
                "JSA_contrib",
                "state_pension",
                "pension_income",
            ],
        )


class UC_income_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reduction from income for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        return max_(
            0,
            benunit("UC_unearned_income", period)
            + UC.means_test.reduction_rate
            * benunit("UC_earned_income", period),
        )


class universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return (
            max_(
                0,
                benunit("UC_maximum_amount", period)
                - benunit("UC_income_reduction", period),
            )
            * benunit("claims_UC", period)
            * benunit("is_UC_eligible", period)
        )
