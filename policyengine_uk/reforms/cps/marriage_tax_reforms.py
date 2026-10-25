from policyengine_uk.model_api import *
from policyengine_uk.utils.income_tax import net_income_from_adjusted_net_income
from policyengine_uk.utils.supplied_inputs import supplied_input
from typing import Union, Optional


def create_expanded_ma_reform(
    max_child_age: Optional[int] = None,
    child_education_levels: Optional[List[str]] = None,
    _parameter_driven: bool = False,
) -> Reform:
    class meets_expanded_ma_conditions(Variable):
        label = "Qualifies for an expanded Marriage Allowance"
        entity = Person
        definition_period = YEAR
        value_type = bool

        def formula(person, period):
            # The couple has a child (a benefit-unit member other than the
            # couple) under the age limit, or meeting the education condition.
            benunit = person.benunit
            is_couple_child = ~person("is_claimant_or_partner", period)
            child_age_limit = max_child_age
            if _parameter_driven:
                cap = person.simulation.tax_benefit_system.parameters(
                    period
                ).gov.contrib.cps.marriage_tax_reforms.expanded_ma.max_child_age
                child_age_limit = cap if cap > 0 else None
            if child_age_limit is not None:
                child_meets_age_condition = is_couple_child & (
                    person("age", period) < child_age_limit
                )
                return benunit.any(child_meets_age_condition)
            if child_education_levels is not None:
                child_meets_education_condition = is_couple_child & np.isin(
                    person("education_level", period).decode_to_str(),
                    child_education_levels,
                )
                return benunit.any(child_meets_education_condition)
            return True

    class meets_marriage_allowance_income_conditions(Variable):
        label = "Meets Marriage Allowance income conditions"
        documentation = "Whether this person (and their partner) meets the conditions for this person to be eligible for the Marriage Allowance, as set out in the Income Tax Act 2007 sections 55B and 55C"
        entity = Person
        definition_period = YEAR
        value_type = bool
        reference = "https://www.legislation.gov.uk/ukpga/2007/3/section/55B"

        def formula(person, period, parameters):
            band = person("tax_band", period)
            eligible_bands = parameters(
                period
            ).gov.hmrc.income_tax.allowances.marriage_allowance.eligible_bands
            base_eligible = np.isin(band.decode_to_str(), eligible_bands)
            # Expand to higher bands if the reform's expansion conditions are met.
            bands = band.possible_values
            expansion = person("meets_expanded_ma_conditions", period) & (
                (band == bands.HIGHER) | (band == bands.ADDITIONAL)
            )
            return base_eligible | expansion

    class marriage_allowance(Variable):
        value_type = float
        entity = Person
        label = "Marriage Allowance"
        definition_period = YEAR
        reference = "https://www.legislation.gov.uk/ukpga/2007/3/part/3/chapter/3A"
        unit = GBP

        def formula(person, period, parameters):
            marital = person("marital_status", period)
            married = marital == marital.possible_values.MARRIED
            eligible = (
                married
                & person("is_claimant_or_partner", period)
                & person("meets_marriage_allowance_income_conditions", period)
            )
            transferable_amount = person("partners_unused_personal_allowance", period)
            allowances = parameters(period).gov.hmrc.income_tax.allowances
            capped_percentage = allowances.marriage_allowance.max
            expanded_ma_cap = parameters(
                period
            ).gov.contrib.cps.marriage_tax_reforms.expanded_ma.ma_rate
            capped_percentage = where(
                person("meets_expanded_ma_conditions", period),
                expanded_ma_cap,
                capped_percentage,
            )
            max_amount = allowances.personal_allowance.amount * capped_percentage
            amount_if_eligible_pre_rounding = max_(
                min_(transferable_amount, max_amount), 0
            )
            # Round up.
            rounding_increment = allowances.marriage_allowance.rounding_increment
            amount_if_eligible = (
                np.ceil(amount_if_eligible_pre_rounding / rounding_increment)
                * rounding_increment
            )
            takes_up = person("would_claim_marriage_allowance", period)
            return eligible * amount_if_eligible * takes_up

    class reform(Reform):
        def apply(self):
            self.add_variable(meets_expanded_ma_conditions)
            self.update_variable(meets_marriage_allowance_income_conditions)
            self.update_variable(marriage_allowance)

    return reform


def create_marriage_neutral_income_tax_reform(
    max_child_age: Optional[int] = None,
    child_education_levels: Optional[List[str]] = None,
    _parameter_driven: bool = False,
) -> Reform:
    class meets_ma_neutral_tax_conditions(Variable):
        label = "Qualifies for an expanded Marriage Allowance"
        entity = Person
        definition_period = YEAR
        value_type = bool

        def formula(person, period):
            # The couple has a child (a benefit-unit member other than the
            # couple) under the age limit, or meeting the education condition.
            benunit = person.benunit
            is_couple_child = ~person("is_claimant_or_partner", period)
            child_age_limit = max_child_age
            if _parameter_driven:
                cap = person.simulation.tax_benefit_system.parameters(
                    period
                ).gov.contrib.cps.marriage_tax_reforms.marriage_neutral_it.max_child_age
                child_age_limit = cap if cap > 0 else None
            if child_age_limit is not None:
                child_meets_age_condition = is_couple_child & (
                    person("age", period) < child_age_limit
                )
                return benunit.any(child_meets_age_condition)
            if child_education_levels is not None:
                child_meets_education_condition = is_couple_child & np.isin(
                    person("education_level", period).decode_to_str(),
                    child_education_levels,
                )
                return benunit.any(child_meets_education_condition)
            return True

    class unadjusted_net_income(Variable):
        value_type = float
        entity = Person
        label = "Taxable income after tax reliefs and before allowances"
        definition_period = YEAR
        reference = "Income Tax Act 2007 s. 23"
        unit = GBP

        def formula(person, period, parameters):
            COMPONENTS = [
                "taxable_employment_income",
                "taxable_pension_income",
                "taxable_social_security_income",
                "taxable_self_employment_income",
                "taxable_property_income",
                "taxable_savings_interest_income",
                "taxable_dividend_income",
                "taxable_miscellaneous_income",
            ]
            if parameters(
                period
            ).gov.contrib.ubi_center.basic_income.interactions.include_in_taxable_income:
                COMPONENTS.append("basic_income")
            return max_(0, add(person, period, COMPONENTS))

    class net_income(Variable):
        label = "Optimised net income"
        documentation = (
            "Income before pension relief and Gift Aid adjustments, split equally "
            "between married partners"
        )
        entity = Person
        definition_period = YEAR
        value_type = float

        def formula(person, period, parameters):
            # Supplied ANI takes precedence over this reform's split. Restore
            # gross Gift Aid and relieved pensions, as the baseline inverse does.
            supplied_ani = supplied_input(person, "adjusted_net_income", period)
            if supplied_ani is not None:
                return net_income_from_adjusted_net_income(person, period, supplied_ani)
            income = person("unadjusted_net_income", period)
            # Split between the spouses or civil partners only, never their
            # children.
            couple_member = person("is_claimant_or_partner", period)
            total_income = person.benunit.sum(couple_member * income)
            has_spouse = person.benunit("is_married", period) & couple_member

            originally_split_income_branch = person.simulation.get_branch(
                "originally_split_income", clone_system=True
            )
            originally_split_income_branch.set_input("net_income", period, income)
            originally_split_income_tax = person.benunit.sum(
                originally_split_income_branch.calculate("income_tax", period)
            )

            split_income = where(
                has_spouse & person("meets_ma_neutral_tax_conditions", period),
                total_income / 2,
                income,
            )
            split_income_branch = person.simulation.get_branch(
                "split_income", clone_system=True
            )
            split_income_branch.set_input("net_income", period, split_income)
            split_income_tax = person.benunit.sum(
                split_income_branch.calculate("income_tax", period)
            )

            return where(
                split_income_tax <= originally_split_income_tax,
                split_income,
                income,
            )

    class reform(Reform):
        def apply(self):
            self.add_variable(meets_ma_neutral_tax_conditions)
            self.update_variable(net_income)
            self.add_variable(unadjusted_net_income)

    return reform


def create_marriage_tax_reform(parameters, period):
    cps = parameters(period).gov.contrib.cps.marriage_tax_reforms
    remove_income_condition = cps.expanded_ma.remove_income_condition
    rate = cps.expanded_ma.ma_rate
    # The expanded Marriage Allowance switches on from its own parameters
    # only: its switch, or a rate other than its own unreformed value.
    # Comparing the rate with the statutory rate instead would switch it on
    # whenever the statutory rate changed, replacing that rate with the
    # reform's and opening the allowance to higher-rate taxpayers (#2551).
    unreformed = parameters.baseline.gov.contrib.cps.marriage_tax_reforms
    default_rate = unreformed.expanded_ma.ma_rate(period)
    ma_max_child_age = cps.expanded_ma.max_child_age
    neutralise_income_tax = cps.marriage_neutral_it.neutralise_income_tax
    it_max_child_age = cps.marriage_neutral_it.max_child_age

    if remove_income_condition or rate != default_rate:
        ma_reform = create_expanded_ma_reform(
            max_child_age=ma_max_child_age if ma_max_child_age > 0 else None,
        )
    else:
        ma_reform = None
    if neutralise_income_tax:
        it_reform = create_marriage_neutral_income_tax_reform(
            max_child_age=it_max_child_age if it_max_child_age > 0 else None,
        )
    else:
        it_reform = None

    if ma_reform is not None:
        if it_reform is not None:
            return ma_reform, it_reform
        else:
            return ma_reform
    else:
        if it_reform is not None:
            return it_reform
        else:
            return None


# Module-level reform instances for use in YAML tests (reference by dotted import path).
# These build the reform classes with no child-age / education conditions, so the reform
# applies to every married couple regardless of child presence.
expanded_ma_reform = create_expanded_ma_reform()
marriage_neutral_it_reform = create_marriage_neutral_income_tax_reform()


def create_period_aware_marriage_tax_reform(parameters, period):
    """Install only families with a real activation in their finite history.

    This constructor dispatch differs from the public period-only factory:
    an available route still chooses its policy separately in each year.
    """
    from policyengine_uk.reforms.reforms import (
        finite_parameter_activation,
        apply_period_aware_reform,
    )

    prefix = "gov.contrib.cps.marriage_tax_reforms."
    paths = (
        "expanded_ma.remove_income_condition",
        "expanded_ma.ma_rate",
        "expanded_ma.max_child_age",
        "marriage_neutral_it.neutralise_income_tax",
        "marriage_neutral_it.max_child_age",
    )
    current = [parameters.get_child(prefix + path) for path in paths]
    baseline = [parameters.baseline.get_child(prefix + path) for path in paths]
    expanded = finite_parameter_activation(
        current + baseline, lambda values: bool(values[0]) or values[1] != values[6]
    )
    neutral = finite_parameter_activation(
        current + baseline, lambda values: bool(values[3])
    )
    if not expanded and not neutral:
        return None

    def expanded_active(root, year):
        p = root(year).gov.contrib.cps.marriage_tax_reforms.expanded_ma
        return (
            p.remove_income_condition
            or p.ma_rate
            != root.baseline(
                year
            ).gov.contrib.cps.marriage_tax_reforms.expanded_ma.ma_rate
        )

    def neutral_active(root, year):
        return root(
            year
        ).gov.contrib.cps.marriage_tax_reforms.marriage_neutral_it.neutralise_income_tax

    class reform(Reform):
        def apply(self):
            if expanded:
                apply_period_aware_reform(
                    self,
                    create_expanded_ma_reform(_parameter_driven=True),
                    (
                        "meets_marriage_allowance_income_conditions",
                        "marriage_allowance",
                    ),
                    expanded_active,
                )
            if neutral:
                apply_period_aware_reform(
                    self,
                    create_marriage_neutral_income_tax_reform(_parameter_driven=True),
                    ("net_income",),
                    neutral_active,
                )

    return reform
