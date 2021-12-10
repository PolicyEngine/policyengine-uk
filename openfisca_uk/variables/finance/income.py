from openfisca_uk.tools.general import *
from openfisca_uk.entities import *


class earned_income(Variable):
    value_type = float
    entity = Person
    label = u"Total earned income"
    definition_period = YEAR

    def formula(person, period, parameters):
        COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "pension_income",
        ]
        return add(person, period, COMPONENTS)


class sublet_income(Variable):
    value_type = float
    entity = Person
    label = u"Income received from sublet agreements"
    definition_period = YEAR


class miscellaneous_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from other sources"
    definition_period = YEAR


class private_transfer_income(Variable):
    value_type = float
    entity = Person
    label = u"Private transfers"
    definition_period = YEAR


class lump_sum_income(Variable):
    value_type = float
    entity = Person
    label = u"Lump sum income"
    definition_period = YEAR


class market_income(Variable):
    value_type = float
    entity = Person
    label = u"Market income"
    definition_period = YEAR

    def formula(person, period, parameters):
        return (
            add(
                person,
                period,
                [
                    "employment_income",
                    "self_employment_income",
                    "savings_interest_income",
                    "dividend_income",
                    "miscellaneous_income",
                    "property_income",
                    "pension_income",
                    "private_transfer_income",
                    "maintenance_income",
                ],
            )
            - person("maintenance_expenses", period)
        )


class gross_income(Variable):
    value_type = float
    entity = Person
    label = u"Gross income, including benefits"
    definition_period = YEAR

    def formula(person, period, parameters):
        COMPONENTS = [
            "employment_income",
            "pension_income",
            "self_employment_income",
            "property_income",
            "savings_interest_income",
            "dividend_income",
            "miscellaneous_income",
            "benefits",
        ]
        return add(person, period, COMPONENTS)


class household_gross_income(Variable):
    value_type = float
    entity = Household
    unit = "currency-GBP"
    label = u"Household gross income"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household.sum(household.members("gross_income", period))


class net_income(Variable):
    value_type = float
    entity = Person
    label = u"Net income"
    documentation = "Market income, minus taxes, plus benefits"
    unit = "currency-GBP"
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("gross_income", period) - person("tax", period)


class hours_worked(Variable):
    value_type = float
    entity = Person
    label = u"Total amount of hours worked by this person"
    definition_period = YEAR


class in_work(Variable):
    value_type = bool
    entity = Person
    label = u"Worked some hours"
    definition_period = YEAR

    def formula(person, period, parameters):
        has_hours_worked = person("hours_worked", period) > 0
        has_earnings = (
            add(
                person, period, ["employment_income", "self_employment_income"]
            )
            > 0
        )
        return has_hours_worked | has_earnings


class weekly_hours(Variable):
    value_type = float
    entity = Person
    label = u"Weekly hours"
    documentation = "Average weekly hours worked"
    definition_period = YEAR
    unit = "hour"

    def formula(person, period, parameters):
        return person("hours_worked", period) / WEEKS_IN_YEAR


class EmploymentStatus(Enum):
    FT_EMPLOYED = "Full-time employed"
    PT_EMPLOYED = "Part-time employed"
    FT_SELF_EMPLOYED = "Full-time self-employed"
    PT_SELF_EMPLOYED = "Part-time self-employed"
    UNEMPLOYED = "Unemployed"
    RETIRED = "Retired"
    STUDENT = "Student"
    CARER = "Carer"
    LONG_TERM_DISABLED = "Long-term sick/disabled"
    SHORT_TERM_DISABLED = "Short-term sick/disabled"
    OTHER_INACTIVE = "Inactive for another reason"
    CHILD = "Child"


class employment_status(Variable):
    value_type = Enum
    entity = Person
    possible_values = EmploymentStatus
    default_value = EmploymentStatus.UNEMPLOYED
    label = u"Employment status of the person"
    definition_period = YEAR


class capital_income(Variable):
    value_type = float
    entity = Person
    label = u"Income from savings or dividends"
    definition_period = YEAR

    def formula(person, period, parameters):
        return add(
            person, period, ["savings_interest_income", "dividend_income"]
        )


class maintenance_income(Variable):
    value_type = float
    entity = Person
    label = u"Maintenance payments"
    definition_period = YEAR


class household_net_income(Variable):
    value_type = float
    entity = Household
    label = u"Household net income"
    documentation = "Disposable income for the household"
    unit = "currency-GBP"
    definition_period = YEAR

    def formula(household, period, parameters):
        gross_income = household("household_gross_income", period)
        tax = household("household_tax", period)
        return gross_income - tax


class household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Household net income, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("household_net_income", period) - household(
            "housing_costs", period
        )


class equiv_household_net_income(Variable):
    value_type = float
    entity = Household
    label = u"Equivalised household net income"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("household_net_income", period) / household(
            "household_equivalisation_bhc", period
        )


class equiv_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = u"Equivalised household net income, after housing costs"
    definition_period = YEAR

    def formula(household, period, parameters):
        return household("household_net_income_ahc", period) / household(
            "household_equivalisation_ahc", period
        )


class base_net_income(Variable):
    value_type = float
    entity = Person
    label = "Existing net income for the person to use as a base in microsimulation"
    definition_period = YEAR


class is_apprentice(Variable):
    value_type = bool
    entity = Person
    label = u"In an apprenticeship programme"
    definition_period = YEAR
    default_value = False


class MinimumWageCategory(Enum):
    APPRENTICE = "Apprentice"
    UNDER_18 = "Under 18"
    BETWEEN_18_20 = "18 to 20"
    BETWEEN_21_22 = "21 to 22"
    BETWEEN_23_24 = "23 to 24"
    OVER_24 = "25 or over"


class minimum_wage_category(Variable):
    value_type = Enum
    possible_values = MinimumWageCategory
    default_value = MinimumWageCategory.OVER_24
    entity = Person
    label = "Minimum wage category"
    definition_period = YEAR

    def formula(person, period, parameters):
        age = person("age", period)
        return select(
            [
                person("is_apprentice", period),
                age < 18,
                (age >= 18) & (age <= 20),
                (age >= 21) & (age <= 22),
                (age >= 23) & (age <= 24),
                age >= 25,
            ],
            [
                MinimumWageCategory.APPRENTICE,
                MinimumWageCategory.UNDER_18,
                MinimumWageCategory.BETWEEN_18_20,
                MinimumWageCategory.BETWEEN_21_22,
                MinimumWageCategory.BETWEEN_23_24,
                MinimumWageCategory.OVER_24,
            ],
        )


class minimum_wage(Variable):
    value_type = float
    entity = Person
    label = u"Minimum wage"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(person, period, parameters):
        MW = parameters(period).law.minimum_wage
        return MW[person("minimum_wage_category", period)]


class household_market_income(Variable):
    value_type = float
    entity = Household
    label = u"Household market income"
    documentation = "Market income for the household"
    definition_period = YEAR
    unit = "currency-GBP"

    def formula(household, period, parameters):
        return household.sum(household.members("market_income", period))
