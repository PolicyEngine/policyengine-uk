from policyengine_uk.model_api import *
from policyengine_uk.variables.household.demographic.household import (
    TenureType,
)


class legacy_benefits(Variable):
    label = "Legacy benefits"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    adds = [
        "JSA_income",
        "housing_benefit",
        "income_support",
        "ESA_income",
        "working_tax_credit",
        "child_tax_credit",
    ]


class would_claim_UC(Variable):
    value_type = bool
    entity = BenUnit
    label = "Would claim Universal Credit"
    documentation = (
        "Whether this family would claim Universal Credit if eligible"
    )
    definition_period = YEAR

    def formula(benunit, period, parameters):
        on_legacy_benefits = benunit("claims_legacy_benefits", period)
        claims_all_entitled_benefits = benunit(
            "claims_all_entitled_benefits", period
        )
        current_uc_claimant = (
            add(benunit, period, ["universal_credit_reported"]) > 0
        )
        baseline_uc = (
            benunit("baseline_universal_credit_entitlement", period) > 0
        )
        eligible = benunit("universal_credit_entitlement", period) > 0
        takeup_rate = parameters(period).gov.dwp.universal_credit.takeup
        return select(
            [
                current_uc_claimant
                | (claims_all_entitled_benefits & ~on_legacy_benefits),
                (~baseline_uc & eligible & ~on_legacy_benefits),
            ],
            [
                True,  # Claims Universal Credit in the baseline
                random(benunit) < takeup_rate,
            ],
            default=False,  # Always non-claimant
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
    unit = GBP


class UC_maximum_amount(Variable):
    value_type = float
    entity = BenUnit
    label = "maximum Universal Credit amount"
    documentation = (
        "This is your total entitlement, before reduction due to income."
    )
    definition_period = YEAR
    unit = GBP
    defined_for = "is_UC_eligible"
    adds = [
        "UC_standard_allowance",
        "UC_child_element",
        "UC_disability_elements",
        "UC_carer_element",
        "UC_housing_costs_element",
        "UC_childcare_element",
    ]


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
    unit = GBP

    def formula(benunit, period, parameters):
        SA = parameters(period).gov.dwp.universal_credit.standard_allowance
        return SA.amount[benunit("UC_claimant_type", period)] * MONTHS_IN_YEAR


class is_child_born_before_child_limit(Variable):
    value_type = bool
    entity = Person
    label = "Born before child limit (exempt)"
    definition_period = YEAR

    def formula(person, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
        start_year = UC.elements.child.limit.start_year
        birth_year = person("birth_year", period)
        if (
            hasattr(person.simulation, "dataset")
            and "frs" in person.simulation.dataset.name
        ):
            # FRS data is based on 2019 populations, so we should add (year - 2019) to the start year to account for
            # the time-fixed nature of the child limit. This should probably be revisited for a more robust solution.
            birth_year = birth_year + (period.start.year - 10)
        born_before_limit = birth_year < start_year
        return person("is_child", period) & born_before_limit


class UC_individual_child_element(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit child element"
    documentation = "For this child, given Universal Credit eligibility"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
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
                    is_eligible,
                ],
                [
                    UC.elements.child.first.higher_amount,
                    UC.elements.child.amount,
                ],
                default=0,
            )
            * MONTHS_IN_YEAR
        )


class uc_child_limit_affected(Variable):
    label = "affected by the UC child limit"
    documentation = "Whether this family is affected by the UC child limit"
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        person = benunit.members
        UC = parameters(period).gov.dwp.universal_credit
        child_index = person("child_index", period)
        born_before_limit = person("is_child_born_before_child_limit", period)
        child_limit_applying = where(
            ~born_before_limit, UC.elements.child.limit.child_count, inf
        )
        is_eligible = (child_index != -1) & (
            child_index <= child_limit_applying
        )
        return benunit.any(~is_eligible & (child_index != -1)) & (
            benunit("universal_credit", period) > 0
        )


class num_UC_eligible_children(Variable):
    value_type = int
    entity = BenUnit
    label = "Children eligible for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        children_born_before_limit = add(
            benunit, period, ["is_child_born_before_child_limit"]
        )
        child_limit = parameters(
            period
        ).gov.dwp.universal_credit.elements.child.limit.child_count
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
    unit = GBP

    adds = ["UC_individual_child_element"]


class UC_carer_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit carer element"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
        has_carer = benunit("benunit_has_carer", period)
        return UC.elements.carer.amount * has_carer * MONTHS_IN_YEAR


class UC_housing_costs_element(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit housing costs element"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        tenure_type = benunit.value_from_first_person(
            benunit.members.household("tenure_type", period)
        )
        rent = benunit("benunit_rent", period)
        max_housing_costs = select(
            [
                (tenure_type == TenureType.RENT_FROM_COUNCIL)
                | (tenure_type == TenureType.RENT_FROM_HA),
                tenure_type == TenureType.RENT_PRIVATELY,
            ],
            [rent, min_(benunit("LHA_cap", period), rent)],
            default=0,
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
            | person("dla_sc_middle_plus", period)
            | (person("pip_dl", period) > 0)
            | (person("attendance_allowance", period) > 0)
            | person("receives_carers_allowance", period)
        )


class UC_individual_non_dep_deduction(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit non-dependent deduction (individual)"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        not_rent_liable = person.benunit("benunit_rent", period) == 0
        over_21 = person("age", period) >= 21
        exempt = person("UC_non_dep_deduction_exempt", period)
        deduction = parameters(
            period
        ).gov.dwp.universal_credit.elements.housing.non_dep_deduction
        return deduction * ~exempt * over_21 * not_rent_liable * MONTHS_IN_YEAR


class UC_non_dep_deductions(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit non-dependent deductions"
    definition_period = YEAR
    unit = GBP

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
    unit = GBP

    def formula(benunit, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
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
    unit = GBP
    defined_for = "is_disabled_for_benefits"

    def formula(person, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
        return (
            person("is_child", period) * UC.elements.child.disabled.amount
        ) * MONTHS_IN_YEAR


class UC_individual_severely_disabled_child_element(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit severely disabled child element"
    definition_period = YEAR
    unit = GBP
    defined_for = "is_severely_disabled_for_benefits"

    def formula(person, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
        return (
            person("is_child", period)
            * UC.elements.child.severely_disabled.amount
        ) * MONTHS_IN_YEAR


class UC_disability_elements(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit disability elements"
    definition_period = YEAR
    unit = GBP

    adds = [
        "UC_individual_disabled_child_element",
        "UC_individual_severely_disabled_child_element",
        "UC_LCWRA_element",
    ]


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
        UC = parameters(period).gov.dwp.universal_credit
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
    unit = GBP
    defined_for = "UC_childcare_work_condition"

    def formula(benunit, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
        eligible_childcare_expenses = add(
            benunit, period, ["childcare_expenses"]
        )
        covered_expenses = (
            eligible_childcare_expenses * UC.elements.childcare.coverage_rate
        )
        return min_(benunit("UC_maximum_childcare", period), covered_expenses)


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
    unit = GBP
    defined_for = "is_UC_work_allowance_eligible"

    def formula(benunit, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
        housing = benunit("UC_housing_costs_element", period)
        monthly_allowance = where(
            housing > 0,
            UC.means_test.work_allowance_with_housing,
            UC.means_test.work_allowance_without_housing,
        )
        return monthly_allowance * MONTHS_IN_YEAR


class UC_earned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit earned income (after disregards and tax)"
    definition_period = YEAR
    unit = GBP

    def formula(benunit, period, parameters):
        personal_gross_earned_income = add(
            benunit, period, ["UC_MIF_capped_earned_income"]
        )
        disregards = add(
            benunit,
            period,
            ["UC_work_allowance", "benunit_tax", "pension_contributions"],
        )
        return max_(0, personal_gross_earned_income - disregards)


class UC_unearned_income(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit unearned income"
    definition_period = YEAR
    unit = GBP
    adds = [
        "carers_allowance",
        "JSA_contrib",
        "pension_income",
        "savings_interest_income",
        "dividend_income",
        "property_income",
    ]


class UC_income_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = "reduction from income for Universal Credit"
    definition_period = YEAR
    unit = GBP
    defined_for = "is_UC_eligible"

    def formula(benunit, period, parameters):
        UC = parameters(period).gov.dwp.universal_credit
        earned_income_reduction = UC.means_test.reduction_rate * benunit(
            "UC_earned_income", period
        )
        unearned_income_reduction = benunit("UC_unearned_income", period)
        maximum_UC = benunit("UC_maximum_amount", period)
        return min_(
            maximum_UC,
            max_(0, earned_income_reduction + unearned_income_reduction),
        )


class universal_credit_entitlement(Variable):
    label = "UC entitlement"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["UC_maximum_amount"]
    subtracts = ["UC_income_reduction"]


class universal_credit_pre_benefit_cap(Variable):
    value_type = float
    entity = BenUnit
    label = "Universal Credit before benefit cap"
    documentation = "Total entitlement to Universal Credit"
    definition_period = YEAR
    unit = GBP
    category = BENEFIT
    adds = ["UC_maximum_amount"]
    subtracts = ["UC_income_reduction"]
    defined_for = "would_claim_UC"


class universal_credit(Variable):
    label = "Universal Credit"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(benunit, period, parameters):
        uc_entitlement = benunit("universal_credit_pre_benefit_cap", period)
        return where(
            uc_entitlement > 0,
            max_(0, uc_entitlement),
            0,
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
    unit = GBP

    def formula(person, period, parameters):
        expected_hours = parameters(
            period
        ).gov.dwp.universal_credit.work_requirements.default_expected_hours
        return person("minimum_wage", period) * expected_hours * WEEKS_IN_YEAR


class UC_MIF_capped_earned_income(Variable):
    value_type = float
    entity = Person
    label = "Universal Credit gross earned income (incl. MIF)"
    documentation = (
        "Gross earned income for UC, with MIF applied where applicable"
    )
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        INCOME_COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "miscellaneous_income",
        ]
        bi = parameters(period).gov.contrib.ubi_center.basic_income
        if bi.interactions.include_in_means_tests:
            INCOME_COMPONENTS.append("basic_income")
        personal_gross_earned_income = add(person, period, INCOME_COMPONENTS)
        floor = where(
            person("UC_MIF_applies", period),
            person("UC_minimum_income_floor", period),
            -inf,
        )
        return max_(personal_gross_earned_income, floor)


class baseline_universal_credit_entitlement(Variable):
    label = "Universal Credit entitlement (baseline)"
    entity = BenUnit
    definition_period = YEAR
    value_type = float
    unit = GBP


class uc_has_entitlement(Variable):
    label = "entitled to Universal Credit"
    documentation = "Whether this family's Universal Credit entitlement is greater than zero."
    entity = BenUnit
    definition_period = YEAR
    value_type = bool

    def formula(benunit, period, parameters):
        return benunit("universal_credit", period) > 0
