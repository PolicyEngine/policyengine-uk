from policyengine_uk.model_api import *


class earned_income(Variable):
    value_type = float
    entity = Person
    label = "Total earned income"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        COMPONENTS = [
            "employment_income",
            "self_employment_income",
            "pension_income",
        ]
        return add(person, period, COMPONENTS)


class market_income(Variable):
    value_type = float
    entity = Person
    label = "Market income"
    documentation = "Income from market sources"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        INCOME_VARIABLES = [
            "employment_income",
            "self_employment_income",
            "savings_interest_income",
            "dividend_income",
            "miscellaneous_income",
            "property_income",
            "pension_income",
            "private_transfer_income",
            "maintenance_income",
        ]
        income = add(person, period, INCOME_VARIABLES)
        return income - person("maintenance_expenses", period)


class gross_income(Variable):
    value_type = float
    entity = Person
    label = "Gross income, including benefits"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        COMPONENTS = [
            "market_income",
            "benefits",
        ]
        return add(person, period, COMPONENTS)


class household_gross_income(Variable):
    value_type = float
    entity = Household
    unit = GBP
    label = "Household gross income"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        return add(
            household,
            period,
            ["household_market_income", "household_benefits"],
        )


class net_income(Variable):
    value_type = float
    entity = Person
    label = "Net income"
    documentation = "Market income, minus taxes, plus benefits"
    unit = GBP
    definition_period = YEAR

    def formula(person, period, parameters):
        return person("gross_income", period) - person("tax", period)


class hours_worked(Variable):
    value_type = float
    entity = Person
    label = "Total amount of hours worked by this person"
    definition_period = YEAR
    unit = "hour"


class in_work(Variable):
    value_type = bool
    entity = Person
    label = "Worked some hours"
    definition_period = YEAR

    def formula(person, period, parameters):
        has_hours_worked = person("hours_worked", period) > 0
        earnings = add(
            person, period, ["employment_income", "self_employment_income"]
        )
        has_earnings = earnings > 0
        return has_hours_worked | has_earnings


class weekly_hours(Variable):
    value_type = float
    entity = Person
    label = "Weekly hours"
    documentation = "Average weekly hours worked"
    definition_period = YEAR
    unit = "hour"
    quantity_type = FLOW

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
    label = "Employment status of the person"
    definition_period = YEAR


class capital_income(Variable):
    value_type = float
    entity = Person
    label = "Income from savings or dividends"
    definition_period = YEAR
    unit = GBP

    adds = ["savings_interest_income", "dividend_income"]


class hbai_household_net_income(Variable):
    value_type = float
    entity = Household
    label = "Household net income (HBAI definition)"
    documentation = "Disposable income for the household, following the definition used for official poverty statistics"
    unit = GBP
    definition_period = YEAR

    adds = ["household_gross_income"]
    subtracts = ["household_tax", "baseline_hbai_excluded_income"]


class household_net_income(Variable):
    label = "net income"
    documentation = "Household net income after taxes and benefits"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = ["household_market_income", "household_benefits"]
    subtracts = ["household_tax"]


class real_household_net_income(Variable):
    label = "Real household net income"
    documentation = "Disposable income in January 2015 prices"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        def cpi(period):
            return parameters(period).calibration.uprating.CPI

        multiplier = cpi("2015-01-01") / cpi(period)
        return household("household_net_income", period) * multiplier


class hbai_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = "Household net income, after housing costs"
    definition_period = YEAR
    unit = GBP

    adds = ["hbai_household_net_income"]
    subtracts = ["housing_costs"]


class equiv_household_net_income(Variable):
    value_type = float
    entity = Household
    label = "Equivalised household net income"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        income = household("household_net_income", period)
        equivalisation = household("household_equivalisation_bhc", period)
        return income / equivalisation


class equiv_hbai_household_net_income(Variable):
    value_type = float
    entity = Household
    label = "Equivalised household net income (HBAI)"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        income = household("hbai_household_net_income", period)
        equivalisation = household("household_equivalisation_bhc", period)
        return income / equivalisation


class equiv_hbai_household_net_income_ahc(Variable):
    value_type = float
    entity = Household
    label = "Equivalised household net income, after housing costs (HBAI)"
    definition_period = YEAR
    unit = GBP

    def formula(household, period, parameters):
        income = household("hbai_household_net_income_ahc", period)
        equivalisation = household("household_equivalisation_ahc", period)
        return income / equivalisation


class base_net_income(Variable):
    value_type = float
    entity = Person
    label = "Existing net income for the person to use as a base in microsimulation"
    definition_period = YEAR
    unit = GBP


class is_apprentice(Variable):
    value_type = bool
    entity = Person
    label = "In an apprenticeship programme"
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
            ],
            [
                MinimumWageCategory.APPRENTICE,
                MinimumWageCategory.UNDER_18,
                MinimumWageCategory.BETWEEN_18_20,
                MinimumWageCategory.BETWEEN_21_22,
                MinimumWageCategory.BETWEEN_23_24,
            ],
            default=MinimumWageCategory.OVER_24,
        )


class minimum_wage(Variable):
    value_type = float
    entity = Person
    label = "Minimum wage"
    definition_period = YEAR
    unit = GBP

    def formula(person, period, parameters):
        MW = parameters(period).gov.hmrc.minimum_wage
        return MW[person("minimum_wage_category", period)]


class household_market_income(Variable):
    value_type = float
    entity = Household
    label = "market income"
    documentation = "Market income for the household"
    definition_period = YEAR
    unit = GBP
    adds = [
        "employment_income",
        "self_employment_income",
        "savings_interest_income",
        "dividend_income",
        "miscellaneous_income",
        "property_income",
        "pension_income",
        "private_transfer_income",
        "maintenance_income",
    ]


class household_income_decile(Variable):
    label = "household income decile"
    documentation = "Decile of household income (person-weighted)"
    entity = Household
    definition_period = YEAR
    value_type = int

    def formula(household, period, parameters):
        income = household("household_net_income", period)
        count_people = household("household_count_people", period)
        household_weight = household("household_weight", period)
        weighted_income = MicroSeries(
            income, weights=household_weight * count_people
        )
        return weighted_income.decile_rank().values


class income_decile(Variable):
    label = "income decile"
    documentation = "Decile of household net income. Households are sorted by disposable income, and then divided into 10 equally-populated groups."
    entity = Person
    definition_period = YEAR
    value_type = int

    def formula(person, period, parameters):
        return person.household("household_income_decile", period)
