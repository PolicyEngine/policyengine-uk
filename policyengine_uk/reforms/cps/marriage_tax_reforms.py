from policyengine_uk.model_api import *
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
                child_meets_age_condition = (
                    person("age", period) <= max_child_age
                )
                return benunit.any(child_meets_age_condition)
            if child_education_levels is not None:
                child_meets_education_condition = np.is_in(
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

        def formula(person, period):
            band = person("tax_band", period)
            bands = band.possible_values
            return (
                (band == bands.BASIC)
                | (band == bands.STARTER)
                | (band == bands.INTERMEDIATE)
                | (  # Expand to higher bands if reform conditions are met.
                    person("meets_expanded_ma_conditions", period)
                    & ((band == bands.HIGHER) | (band == bands.ADDITIONAL))
                )
            )

    class marriage_allowance(Variable):
        value_type = float
        entity = Person
        label = "Marriage Allowance"
        definition_period = YEAR
        reference = (
            "https://www.legislation.gov.uk/ukpga/2007/3/part/3/chapter/3A"
        )
        unit = GBP

        def formula(person, period, parameters):
            marital = person("marital_status", period)
            married = marital == marital.possible_values.MARRIED
            eligible = married & person(
                "meets_marriage_allowance_income_conditions", period
            )
            transferable_amount = person(
                "partners_unused_personal_allowance", period
            )
            allowances = parameters(period).gov.hmrc.income_tax.allowances
            takeup_rate = allowances.marriage_allowance.takeup_rate
            capped_percentage = allowances.marriage_allowance.max
            expanded_ma_cap = parameters(
                period
            ).gov.contrib.cps.marriage_tax_reforms.expanded_ma.ma_rate
            capped_percentage = where(
                person("meets_expanded_ma_conditions", period),
                expanded_ma_cap,
                capped_percentage,
            )
            max_amount = (
                allowances.personal_allowance.amount * capped_percentage
            )
            amount_if_eligible_pre_rounding = min_(
                transferable_amount, max_amount
            )
            # Round up.
            rounding_increment = (
                allowances.marriage_allowance.rounding_increment
            )
            amount_if_eligible = (
                np.ceil(amount_if_eligible_pre_rounding / rounding_increment)
                * rounding_increment
            )
            takes_up = random(person) < takeup_rate
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
                child_meets_age_condition = (
                    person("age", period) <= max_child_age
                )
                return benunit.any(child_meets_age_condition)
            if child_education_levels is not None:
                child_meets_education_condition = np.is_in(
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
            split_income_branch.set_input(
                "adjusted_net_income", period, split_income
            )
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
