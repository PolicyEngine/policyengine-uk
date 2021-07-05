from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.general import *


class universal_credit_reported(Variable):
    value_type = float
    entity = Person
    label = u"Reported amount of Universal Credit"
    definition_period = YEAR


class claims_UC(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether this family is imputed to claim UC"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        already_claiming = (
            aggr(benunit, period, ["universal_credit_reported"]) > 0
        )
        would_claim = not_(benunit("claims_legacy_benefits", period)) * (
            random(benunit)
            < parameters(period).benefit.tax_credits.working_tax_credit.takeup
        )
        return already_claiming + would_claim


class UC_personal_allowance(Variable):
    value_type = float
    entity = BenUnit
    label = u"Personal allowance for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        is_single = benunit("is_single", period)
        is_couple = benunit("is_couple", period)
        is_over_25 = benunit("youngest_adult_age", period.this_year) >= 25
        basic_amount = (
            is_single * not_(is_over_25) * UC.allowances.basic_single_young
            + is_single * is_over_25 * UC.allowances.basic_single_older
            + is_couple * not_(is_over_25) * UC.allowances.basic_couple_young
            + is_couple * is_over_25 * UC.allowances.basic_couple_older
        ) * MONTHS_IN_YEAR
        return basic_amount


class UC_premiums(Variable):
    value_type = float
    entity = BenUnit
    label = u"Premiums for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        has_carer = (
            aggr(benunit, period.this_year, ["is_carer_for_benefits"]) > 0
        )
        num_eligible_children = min_(2, benunit.nb_persons(BenUnit.CHILD))
        childcare_limit = (
            num_eligible_children == 1
        ) * UC.elements.max_childcare_1 * MONTHS_IN_YEAR + (
            num_eligible_children > 1
        ) * UC.elements.max_childcare_2 * MONTHS_IN_YEAR
        premiums = (
            has_carer * UC.elements.carer_element
            + num_eligible_children * UC.elements.child_element
            + benunit("num_disabled_children", period.this_year)
            * UC.elements.disabled_child_element
            + benunit("num_disabled_adults", period.this_year)
            * UC.elements.disabled_element
        ) * MONTHS_IN_YEAR
        eligible_childcare_costs = benunit.sum(
            benunit.members("childcare_cost", period)
        )
        childcare_element = min_(
            childcare_limit,
            eligible_childcare_costs * UC.elements.childcare_cost_rate,
        )
        return premiums + childcare_element


class UC_eligible_rent(Variable):
    value_type = float
    entity = BenUnit
    label = u"Eligible rent in Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        rent = benunit.max(benunit.members.household("rent", period))
        LHA_cap = benunit("LHA_cap", period)
        LHA_eligible = benunit("LHA_eligible", period)
        eligible_rent = where(LHA_eligible, min_(LHA_cap, rent), rent)
        return eligible_rent


class universal_credit_applicable_amount(Variable):
    value_type = float
    entity = BenUnit
    label = u"Relevant income for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        applicable_amount = (
            benunit("UC_personal_allowance", period)
            + benunit("UC_premiums", period)
            + benunit("UC_eligible_rent", period)
        )
        return applicable_amount


class universal_credit_income_reduction(Variable):
    value_type = float
    entity = BenUnit
    label = u"Reduction from income for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        UC = parameters(period).benefit.universal_credit
        INCOME_COMPONENTS = ["employment_income", "trading_income"]
        earned_income = aggr(benunit, period, INCOME_COMPONENTS)
        unearned_income = aggr(
            benunit,
            period,
            ["carers_allowance", "JSA_contrib", "state_pension"],
            options=[ADD],
        )
        unearned_income += aggr(benunit, period, ["pension_income"])
        earned_income = max_(
            0,
            earned_income
            - aggr(
                benunit,
                period,
                ["income_tax", "national_insurance"],
            ),
        )
        housing_element = benunit("UC_eligible_rent", period)
        earnings_disregard = (
            housing_element > 0
        ) * UC.means_test.earn_disregard_with_housing * MONTHS_IN_YEAR + (
            housing_element == 0
        ) * UC.means_test.earn_disregard * MONTHS_IN_YEAR
        earnings_reduction = max_(0, earned_income - earnings_disregard)
        reduction = max_(
            0,
            unearned_income
            + UC.means_test.reduction_rate * earnings_reduction,
        )
        return reduction


class universal_credit_eligible(Variable):
    value_type = bool
    entity = BenUnit
    label = u"Whether eligible for Universal Credit"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        DISQUALIFYING_BENEFITS = [
            "working_tax_credit",
            "child_tax_credit",
            "housing_benefit",
            "income_support",
            "ESA_income",
            "JSA_income",
        ]
        disqualifying = add(benunit, period, DISQUALIFYING_BENEFITS) + aggr(
            benunit, period, ["SDA"]
        )
        eligible = (disqualifying == 0) * (
            not_(benunit.min(benunit.members("is_SP_age", period)))
        )
        return eligible


class universal_credit(Variable):
    value_type = float
    entity = BenUnit
    label = u"Universal Credit amount"
    definition_period = YEAR

    def formula(benunit, period, parameters):
        eligible = benunit("universal_credit_eligible", period) * benunit(
            "claims_UC", period
        )
        amount = benunit("universal_credit_applicable_amount", period)
        reduction = benunit("universal_credit_income_reduction", period)
        final_amount = eligible * max_(0, amount - reduction)
        capped_amount = min_(final_amount, benunit("benefit_cap", period))
        return capped_amount
