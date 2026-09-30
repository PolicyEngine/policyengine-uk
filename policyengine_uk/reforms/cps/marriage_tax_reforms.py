from policyengine_uk.model_api import *
from policyengine_uk.variables.gov.hmrc.income_tax.allowances.meets_marriage_allowance_income_conditions import (
    liable_only_at_marriage_allowance_rates,
)
from typing import Union, Optional


def create_expanded_ma_reform(
    max_child_age: Optional[int] = None,
    child_education_levels: Optional[List[str]] = None,
) -> Reform:
    class meets_expanded_ma_conditions(Variable):
        label = "Qualifies for an expanded Marriage Allowance"
        entity = Person
        definition_period = YEAR
        value_type = bool

        def formula(person, period):
            # There is a child who either meets the age condition or the education condition
            benunit = person.benunit
            if max_child_age is not None:
                child_meets_age_condition = person("age", period) <= max_child_age
                return benunit.any(child_meets_age_condition)
            if child_education_levels is not None:
                child_meets_education_condition = np.isin(
                    person("education_level", period).decode_to_str(),
                    child_education_levels,
                )
                return benunit.any(child_meets_education_condition)
            return True

    class meets_marriage_allowance_income_conditions(Variable):
        label = "Meets Marriage Allowance income conditions"
        documentation = (
            "Whether this person pays income tax only at the rates that allow "
            "a Marriage Allowance election, or meets the reform's expansion "
            "conditions, which lift that restriction."
        )
        entity = Person
        definition_period = YEAR
        value_type = bool
        reference = "https://www.legislation.gov.uk/ukpga/2007/3/section/55B"

        def formula(person, period, parameters):
            return liable_only_at_marriage_allowance_rates(
                person, period, parameters
            ) | person("meets_expanded_ma_conditions", period)

    class marriage_allowance_transferable_amount(Variable):
        value_type = float
        entity = Person
        label = "Marriage Allowance transferable amount"
        documentation = (
            "The share of the personal allowance a Marriage Allowance election "
            "transfers, at the reform's rate for couples meeting its expansion "
            "conditions, rounded up to the rounding increment."
        )
        definition_period = YEAR
        reference = "https://www.legislation.gov.uk/ukpga/2007/3/section/55B"
        unit = GBP

        def formula(person, period, parameters):
            p = parameters(period)
            allowances = p.gov.hmrc.income_tax.allowances
            share = where(
                person("meets_expanded_ma_conditions", period),
                p.gov.contrib.cps.marriage_tax_reforms.expanded_ma.ma_rate,
                allowances.marriage_allowance.max,
            )
            amount = allowances.personal_allowance.amount * share
            increment = allowances.marriage_allowance.rounding_increment
            return np.ceil(amount / increment) * increment

    class reform(Reform):
        def apply(self):
            self.add_variable(meets_expanded_ma_conditions)
            self.update_variable(meets_marriage_allowance_income_conditions)
            self.update_variable(marriage_allowance_transferable_amount)

    return reform


def create_marriage_neutral_income_tax_reform(
    max_child_age: Optional[int] = None,
    child_education_levels: Optional[List[str]] = None,
) -> Reform:
    class meets_ma_neutral_tax_conditions(Variable):
        label = "Qualifies for an expanded Marriage Allowance"
        entity = Person
        definition_period = YEAR
        value_type = bool

        def formula(person, period):
            # There is a child who either meets the age condition or the education condition
            benunit = person.benunit
            if max_child_age is not None:
                child_meets_age_condition = person("age", period) <= max_child_age
                return benunit.any(child_meets_age_condition)
            if child_education_levels is not None:
                child_meets_education_condition = np.isin(
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

    class adjusted_net_income(Variable):
        label = "Optimised adjusted net income"
        documentation = "Adjusted net income, but split equally between partners if they are married"
        entity = Person
        definition_period = YEAR
        value_type = float

        def formula(person, period, parameters):
            income = person("unadjusted_net_income", period)
            is_adult = person("is_adult", period)
            total_income = person.benunit.sum(is_adult * income)
            has_spouse = person.benunit("is_married", period) & is_adult

            originally_split_income_branch = person.simulation.get_branch(
                "originally_split_income", clone_system=True
            )
            originally_split_income_branch.set_input(
                "adjusted_net_income", period, income
            )
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
            split_income_branch.set_input("adjusted_net_income", period, split_income)
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
            self.update_variable(adjusted_net_income)
            self.add_variable(unadjusted_net_income)

    return reform


def create_marriage_tax_reform(parameters, period):
    cps = parameters(period).gov.contrib.cps.marriage_tax_reforms
    remove_income_condition = cps.expanded_ma.remove_income_condition
    rate = cps.expanded_ma.ma_rate
    original_rate = parameters(
        period
    ).gov.hmrc.income_tax.allowances.marriage_allowance.max
    ma_max_child_age = cps.expanded_ma.max_child_age
    neutralise_income_tax = cps.marriage_neutral_it.neutralise_income_tax
    it_max_child_age = cps.marriage_neutral_it.max_child_age

    if remove_income_condition or rate != original_rate:
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
