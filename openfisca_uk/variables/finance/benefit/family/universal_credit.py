from openfisca_uk.model_api import *
from openfisca_uk.variables.demographic.household import TenureType


class claims_UC(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Universal Credit"
    documentation = (
        "Whether this family would claim Universal Credit if eligible"
    )
    definition_period = YEAR

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
        eligible_and_would_claim_any_legacy_benefits = (
            sum([WTC, CTC, HB, IS, ESA_income, JSA_income]) > 0
        )
        return (
            ~benunit("claims_legacy_benefits", period)
            & eligible_and_would_claim_any_legacy_benefits
        )


class is_UC_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Universal Credit eligible"
    documentation = "Whether this family is eligible for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        return benunit.any(benunit.members("is_WA_adult", period))


class universal_credit_reported(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit (reported)"
    documentation = "Reported amount of Universal Credit"
    definition_period = YEAR
    unit = "currency-GBP"


class UC_maximum_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "Maximum Universal Credit amount"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period):
        ELEMENTS = [
            "UC_standard_allowance",
            "UC_child_element",
            "UC_disability_elements",
            "UC_carer_element",
            "UC_housing_costs_element",
            "UC_childcare_element",
        ]
        return add(benunit, period, ELEMENTS)


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
    label = "UC claimant type"
    documentation = (
        "The category of the UC claimant, assuming their eligibilty to UC"
    )
    definition_period = YEAR

    def formula(benunit, period):
        is_single = benunit("is_single", period)
        any_over_25 = benunit("eldest_adult_age", period.this_year) >= 25
        return select(
            [
                is_single & ~any_over_25,
                is_single & any_over_25,
                ~is_single & ~any_over_25,
                ~is_single & any_over_25,
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
    label = "Universal Credit standard allowance"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        SA = parameters(period).benefit.universal_credit.standard_allowance
        return SA.amount[benunit("UC_claimant_type", period)] * MONTHS_IN_YEAR


class is_child_born_before_child_limit(Variable):
    value_type = bool
    entity = Person
    label = "Born before child limit (exempt)"
    definition_period = YEAR

    def formula(person, period, parameters):
        UC = parameters(period).benefit.universal_credit
        start_year = UC.elements.child.limit.start_year
        born_before_limit = person("birth_year", period) < start_year
        return person("is_child", period) & born_before_limit


class UC_individual_child_element(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit child element"
    documentation = "For this child, given Universal Credit eligibility"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        UC = parameters(period).benefit.universal_credit
        child_index = person("child_index", period)
        born_before_limit = person("is_child_born_before_child_limit", period)
        child_limit_applying = where(
            ~born_before_limit, UC.elements.child.limit.child_count, inf
        )
        is_eligible = (child_index != -1) & (
            child_index <= child_limit_applying
        )
        return (
            select(
                [
                    (child_index == 1) & born_before_limit & is_eligible,
                    child_index == 1 & is_eligible,
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
    label = "Children eligible for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        children_born_before_limit = aggr(
            benunit, period, ["is_child_born_before_child_limit"]
        )
        child_limit = parameters(
            period
        ).benefit.universal_credit.elements.child.limit.child_count
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
    label = "Universal Credit child element"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        return aggr(benunit, period, ["UC_individual_child_element"])


class UC_carer_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit carer element"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        has_carer = benunit("benunit_has_carer", period)
        return UC.elements.carer.amount * has_carer * MONTHS_IN_YEAR


class UC_housing_costs_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit housing costs element"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        tenure_type = benunit.value_from_first_person(
            benunit.members.household("tenure_type", period).decode_to_str()
        )
        rent = benunit("benunit_rent", period)
        max_housing_costs = select(
            [
                np.isin(
                    tenure_type,
                    [
                        TenureType.RENT_FROM_COUNCIL.name,
                        tenure_type == TenureType.RENT_FROM_HA.name,
                    ],
                ),
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


class UC_non_dep_deduction_exempt(Variable):
    value_type = bool
    entity = Person
    label = "Not expected to contribute to housing costs for Universal Credit"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            (person.benunit("pension_credit", period) > 0)
            | person("DLA_SC_middle_plus", period)
            | (person("PIP_DL", period) > 0)
            | (person("AA", period) > 0)
            | person("receives_carers_allowance", period)
        )


class UC_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit non-dependent deduction (individual)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        not_rent_liable = person.benunit("benunit_rent", period) == 0
        over_21 = person("age", period) >= 21
        exempt = person("UC_non_dep_deduction_exempt", period)
        deduction = parameters(
            period
        ).benefit.universal_credit.elements.housing.non_dep_deduction
        return deduction * ~exempt * over_21 * not_rent_liable * MONTHS_IN_YEAR


class UC_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit non-dependent deductions"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        # Deductions are made for non-dependents outside the benefit unit,
        # but within the household, who meet certain conditions. To do this,
        # we first calculate the non-dependent deduction for each person (from
        # the perspective of a different benefit unit). Then, to calculate
        # the deduction for non-dependents outside the benefit unit, we subtract
        # the total non-dependent deductions for the benefit unit members from
        # the deductions for household members.
        deductions = benunit.members("UC_individual_non_dep_deduction", period)
        non_dep_deductions_in_hh = benunit.max(
            benunit.members.household.sum(deductions)
        )
        non_dep_deductions_in_bu = benunit.sum(deductions)
        return non_dep_deductions_in_hh - non_dep_deductions_in_bu


class limited_capability_for_WRA(Variable):
    value_type = bool
    entity = Person
    label = "Assessed to have limited capability for work-related activity"
    documentation = """Whether this person has been assessed by the DWP as having limited capability for work or work-related activity"""
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("is_disabled_for_benefits", period)


class UC_LCWRA_element(Variable):
    value_type = float
    entity = BenUnit
    label = (
        "Universal Credit limited capability for work-related-activity element"
    )
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        person_amounts = (
            benunit.members("limited_capability_for_WRA", period)
            * UC.elements.disabled.amount
        )
        return benunit.sum(person_amounts) * MONTHS_IN_YEAR


class UC_individual_disabled_child_element(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit disabled child element"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        UC = parameters(period).benefit.universal_credit
        return (
            person("is_disabled_for_benefits", period)
            * person("is_child", period)
            * UC.elements.child.disabled.amount
        ) * MONTHS_IN_YEAR


class UC_individual_severely_disabled_child_element(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit severely disabled child element"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        UC = parameters(period).benefit.universal_credit
        return (
            person("is_severely_disabled_for_benefits", period)
            * person("is_child", period)
            * UC.elements.child.severely_disabled.amount
        ) * MONTHS_IN_YEAR


class UC_disability_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit disability elements"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period):
        PERSONAL_ELEMENTS = [
            "UC_individual_disabled_child_element",
            "UC_individual_severely_disabled_child_element",
        ]
        personal_elements = aggr(benunit, period, PERSONAL_ELEMENTS)
        benunit_elements = benunit("UC_LCWRA_element", period)
        return personal_elements + benunit_elements


class UC_childcare_work_condition(Variable):
    value_type = bool
    entity = BenUnit
    label = "Meets Universal Credit childcare work condition"
    definition_period = YEAR
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/32/2020-04-06"
    )

    def formula(benunit, period, parameters):
        person = benunit.members
        adult = person("is_adult", period)
        in_work = person("in_work", period)
        adults_not_in_work = adult & ~in_work
        # Benefit unit must not have any adults not in work.
        return ~benunit.any(adults_not_in_work)


class num_UC_eligible_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Children eligible for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        eligible_child = (
            benunit.members("UC_individual_child_element", period) > 0
        )
        return benunit.sum(eligible_child)


class UC_maximum_childcare(Variable):
    value_type = float
    entity = BenUnit
    label = "Maximum Universal Credit childcare element"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        children = benunit("num_UC_eligible_children", period)
        return (
            UC.elements.childcare.maximum[clip(children, 1, 2)]
            * MONTHS_IN_YEAR
        )


class UC_childcare_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit childcare element"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        eligible_childcare_expenses = aggr(
            benunit, period, ["childcare_expenses"]
        )
        covered_expenses = (
            eligible_childcare_expenses * UC.elements.childcare.coverage_rate
        )
        childcare_element = min_(
            benunit("UC_maximum_childcare", period), covered_expenses
        )
        work_condition = benunit("UC_childcare_work_condition", period)
        return work_condition * childcare_element


class is_UC_work_allowance_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = "Family receives a Universal Credit Work Allowance"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        has_LCWRA = benunit.any(
            benunit.members("limited_capability_for_WRA", period)
        )
        has_children = benunit.any(benunit.members("is_child", period))
        return has_LCWRA | has_children


class UC_work_allowance(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit work allowance"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        housing = benunit("UC_housing_costs_element", period)
        monthly_allowance = where(
            housing > 0,
            UC.means_test.work_allowance_with_housing,
            UC.means_test.work_allowance_without_housing,
        )
        eligible = benunit("is_UC_work_allowance_eligible", period)
        return eligible * monthly_allowance * MONTHS_IN_YEAR


class UC_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income (after disregards and tax)"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        personal_gross_earned_income = aggr(
            benunit, period, ["UC_MIF_capped_earned_income"]
        )
        benunit_disregards = add(
            benunit, period, ["UC_work_allowance", "benunit_tax"]
        )
        person_disregards = aggr(benunit, period, ["pension_contributions"])
        disregards = benunit_disregards + person_disregards
        return max_(0, personal_gross_earned_income - disregards)


class UC_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit unearned income"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        SOURCES = [
            "carers_allowance",
            "JSA_contrib",
            "pension_income",
            "savings_interest_income",
            "dividend_income",
        ]
        return aggr(benunit, period, SOURCES)


class UC_income_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "Reduction from income for Universal Credit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        earned_income_reduction = UC.means_test.reduction_rate * benunit(
            "UC_earned_income", period
        )
        unearned_income_reduction = benunit("UC_unearned_income", period)
        return max_(0, earned_income_reduction + unearned_income_reduction)


class universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(benunit, period, parameters):
        amount = max_(
            0,
            benunit("UC_maximum_amount", period)
            - benunit("UC_income_reduction", period),
        )
        return (
            amount
            * benunit("claims_UC", period)
            * benunit("is_UC_eligible", period)
        )


class UC_MIF_applies(Variable):
    value_type = bool
    entity = Person
    label = "Minimum Income Floor applies"
    documentation = "Whether the Minimum Income Floor should be used to determine UC entitlement"
    reference = (
        "https://www.legislation.gov.uk/uksi/2013/376/regulation/62/2021-04-06"
    )
    definition_period = YEAR

    def formula(person, period, parameters):
        has_profits = person("self_employment_income", period) > 0
        in_startup_period = person("is_in_startup_period", period)
        return has_profits & ~in_startup_period


class is_in_startup_period(Variable):
    value_type = bool
    entity = Person
    label = "In a start-up period"
    documentation = (
        "Whether this person is in a 'start-up' period for Universal Credit"
    )
    definition_period = YEAR
    default_value = False


class UC_minimum_income_floor(Variable):
    value_type = float
    entity = Person
    label = "Minimum Income Floor"
    definition_period = YEAR
    unit = "currency-GBP"
    reference = ""

    def formula(person, period, parameters):
        expected_hours = parameters(
            period
        ).benefit.universal_credit.work_requirements.default_expected_hours
        return person("minimum_wage", period) * expected_hours * WEEKS_IN_YEAR


class UC_MIF_capped_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit gross earned income (incl. MIF)"
    documentation = (
        "Gross earned income for UC, with MIF applied where applicable"
    )
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "miscellaneous_income",
        ]
        personal_gross_earned_income = add(person, period, INCOME_COMPONENTS)
        floor = where(
            person("UC_MIF_applies", period),
            person("UC_minimum_income_floor", period),
            -inf,
        )
        return max_(personal_gross_earned_income, floor)
