from policyengine_uk.model_api import *
import datetime
import numpy as np


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
            "private_pension_income",
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
            "private_pension_income",
            "private_transfer_income",
            "maintenance_income",
        ]
        income = add(person, period, INCOME_VARIABLES)
        return income - person("maintenance_expenses", period)


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

    adds = [
        "household_market_income",
        "child_benefit",
        "esa_income",
        "esa_contrib",
        "housing_benefit",
        "income_support",
        "jsa_income",
        "jsa_contrib",
        "pension_credit",
        "universal_credit",
        "working_tax_credit",
        "child_tax_credit",
        "attendance_allowance",
        "afcs",
        "bsp",
        "carers_allowance",
        "dla",
        "iidb",
        "incapacity_benefit",
        "jsa_contrib",
        "pip",
        "sda",
        "state_pension",
        "maternity_allowance",
        "statutory_sick_pay",
        "statutory_maternity_pay",
        "ssmg",
        "basic_income",
        "cost_of_living_support_payment",
        "winter_fuel_allowance",
        "tax_free_childcare",
        # Reference for tax-free-childcare: https://assets.publishing.service.gov.uk/media/5e7b191886650c744175d08b/households-below-average-income-1994-1995-2018-2019.pdf
    ]
    subtracts = [
        "council_tax",
        "domestic_rates",
        "wealth_tax",
        "income_tax",
        "national_insurance",
    ]


class household_net_income(Variable):
    label = "household net income"
    documentation = "household net income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "household_market_income",
        "household_benefits",
    ]
    subtracts = [
        "household_tax",
    ]

    def formula(household, period, parameters):
        market_income = household("household_market_income", period)
        benefits = household("household_benefits", period)
        tax = household("household_tax", period)
        return np.round(market_income + benefits - tax)


class household_net_income_ahc(Variable):
    label = "household net income"
    documentation = "household net income"
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP
    adds = [
        "household_market_income",
        "household_benefits",
    ]
    subtracts = [
        "household_tax",
        "housing_costs",
    ]

    def formula(household, period, parameters):
        market_income = household("household_market_income", period)
        benefits = household("household_benefits", period)
        tax = household("household_tax", period)
        housing_costs = household("housing_costs", period)
        return np.round(market_income + benefits - tax - housing_costs)


class inflation_adjustment(Variable):
    label = (
        f"inflation multiplier to get {datetime.datetime.now().year} prices"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = "/1"

    def formula(household, period, parameters):
        cpi = parameters.gov.obr.consumer_price_index
        current_period_cpi = cpi(period)
        now_cpi = cpi(datetime.datetime.now().strftime("%Y-01-01"))
        return now_cpi / current_period_cpi


class real_household_net_income(Variable):
    label = (
        f"real household net income ({datetime.datetime.now().year} prices)"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        net_income = household("household_net_income", period)
        return net_income * household("inflation_adjustment", period)


class real_household_net_income_ahc(Variable):
    label = (
        f"real household net income ({datetime.datetime.now().year} prices)"
    )
    entity = Household
    definition_period = YEAR
    value_type = float
    unit = GBP

    def formula(household, period, parameters):
        net_income = household("household_net_income_ahc", period)
        return net_income * household("inflation_adjustment", period)


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
    label = "household market income"
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
        "private_pension_income",
        "private_transfer_income",
        "maintenance_income",
        "capital_gains",
    ]

    def formula(person, period, parameters):
        total = add(person, period, household_market_income.adds)
        contrib = parameters(
            period
        ).gov.contrib.policyengine.economy.gdp_per_capita
        return total * (contrib + 1)


class household_income_decile(Variable):
    label = "household income decile"
    documentation = "Decile of household income (person-weighted)"
    entity = Household
    definition_period = YEAR
    value_type = int

    def formula(household, period, parameters):
        income = household("equiv_hbai_household_net_income", period)
        count_people = household("household_count_people", period)
        household_weight = household("household_weight", period)
        weighted_income = MicroSeries(
            income, weights=household_weight * count_people
        )
        decile = weighted_income.decile_rank().values
        # Set negatives to -1.
        # This avoids the bottom decile summing to a negative number,
        # which would flip the % change in the interface.
        return where(income < 0, -1, decile)


class income_decile(Variable):
    label = "income decile"
    documentation = "Decile of household net income. Households are sorted by disposable income, and then divided into 10 equally-populated groups."
    entity = Person
    definition_period = YEAR
    value_type = int

    def formula(person, period, parameters):
        return person.household("household_income_decile", period)


class household_statutory_maternity_pay(Variable):
    label = "Statutory maternity pay"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP


class household_statutory_paternity_pay(Variable):
    label = "Statutory paternity pay"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP


class household_statutory_sick_pay(Variable):
    label = "Statutory sick pay"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP


class capital_gains(Variable):
    label = "capital gains"
    entity = Person
    definition_period = YEAR
    value_type = float
    unit = GBP
    uprating = "gov.obr.non_labour_income"
    adds = [
        "capital_gains_before_response",
        "capital_gains_behavioural_response",
    ]
