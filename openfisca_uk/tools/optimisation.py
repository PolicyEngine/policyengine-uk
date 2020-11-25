from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.simulation import Simulation
from openfisca_uk.tools.general import *
import numpy as np
from rdbl import gbp

CORE_BENEFITS = [
    "child_benefit",
    "income_support",
    "JSA_contrib",
    "JSA_income",
    "child_tax_credit",
    "working_tax_credit",
    "universal_credit",
    "state_pension",
    "pension_credit",
    "ESA_income",
    "ESA_contrib",
]


def ft_funded_ubi_reform(
    pensioner_amount=175,
    wa_adult_amount=100,
    child_amount=50,
    adult_disability_bonus=0,
    child_disability_bonus=0,
    flat_tax_rate=0.5,
    abolish_benefits=CORE_BENEFITS,
):
    class income_tax(Variable):
        value_type = float
        entity = Person
        label = "Income tax paid per year"
        definition_period = YEAR

        def formula(person, period, parameters):
            return flat_tax_rate * person("taxable_income", period)

    class basic_income(Variable):
        value_type = float
        entity = Person
        label = "Amount of basic income received per week"
        definition_period = WEEK

        def formula(person, period, parameters):
            return (
                pensioner_amount * person("is_SP_age", period.this_year)
                + wa_adult_amount * person("is_WA_adult", period.this_year)
                + child_amount * person("is_child", period.this_year)
                + person("is_disabled", period.this_year)
                * person("is_WA_adult", period.this_year)
                * adult_disability_bonus
                + person("is_disabled", period.this_year)
                * person("is_child", period.this_year)
                * child_disability_bonus
            )

    class benunit_basic_income(Variable):
        value_type = float
        entity = BenUnit
        label = "Amount of basic income per week for the benefit unit"
        definition_period = WEEK

        def formula(benunit, period, parameters):
            return benunit.sum(benunit.members("basic_income", period))

    class household_basic_income(Variable):
        value_type = float
        entity = Household
        label = "Amount of basic income per week for the household"
        definition_period = WEEK

        def formula(household, period, parameters):
            return household.sum(household.members("basic_income", period))

    class gross_income(Variable):
        value_type = float
        entity = Person
        label = "Gross income"
        definition_period = YEAR

        def formula(person, period, parameters):
            COMPONENTS = [
                "basic_income",
                "earnings",
                "profit",
                "state_pension",
                "pension_income",
                "savings_interest",
                "rental_income",
                "SSP",
                "SPP",
                "SMP",
                "holiday_pay",
                "dividend_income",
                "total_benefits",
                "benefits_modelling",
            ]
            return add(person, period, COMPONENTS, options=[MATCH])

    class reform(Reform):
        def apply(self):
            for changed_var in [income_tax, gross_income]:
                self.update_variable(changed_var)
            for added_var in [
                basic_income,
                benunit_basic_income,
                household_basic_income,
            ]:
                self.add_variable(added_var)
            for removed_var in abolish_benefits + ["NI"]:
                self.neutralize_variable(removed_var)

    return reform


def net_cost_of_reform(*reforms, reform, data_dir="frs", period="2020"):
    baseline = Simulation(data_dir=data_dir, input_period=period)
    reformed = Simulation(*reforms, data_dir=data_dir, input_period=period)
    households = baseline.calc("household_weight")
    net_cost = np.sum(
        (
            reformed.calc("household_net_income_ahc")
            - baseline.calc("household_net_income_ahc")
        )
        * households
    )
    return net_cost


def solve_ft_ubi_reform(
    *reforms,
    pensioner_amount=175,
    wa_adult_coef=1,
    child_coef=1,
    adult_disability_coef=0,
    child_disability_coef=0,
    flat_tax_rate=0.5,
    abolish_benefits=CORE_BENEFITS,
    min_cost=-1e9,
    max_cost=0,
    max_steps=16,
    verbose=False,
):
    min_x = 0
    max_x = 200
    x_hist = []
    y_hist = []
    x = (min_x + max_x) / 2
    reform = ft_funded_ubi_reform(
        pensioner_amount=pensioner_amount,
        wa_adult_amount=x * wa_adult_coef,
        child_amount=x * child_coef,
        adult_disability_bonus=x * adult_disability_coef,
        child_disability_bonus=x * child_coef,
        flat_tax_rate=flat_tax_rate,
        abolish_benefits=abolish_benefits,
    )
    y = net_cost_of_reform(*reforms, reform)
    step = 0
    while (y > max_cost or y < min_cost) and step < max_steps:
        step += 1
        x_hist += [x]
        y_hist += [y]
        if y > max_cost:
            max_x = x
        elif y < min_cost:
            min_x = x
        x = (min_x + max_x) / 2
        reform = ft_funded_ubi_reform(
            pensioner_amount=pensioner_amount,
            wa_adult_amount=x * wa_adult_coef,
            child_amount=x * child_coef,
            adult_disability_bonus=x * adult_disability_coef,
            child_disability_bonus=x * child_coef,
            flat_tax_rate=flat_tax_rate,
            abolish_benefits=abolish_benefits,
        )
        y = net_cost_of_reform(reform)
        if verbose:
            print(f"Step {step}: cost = {gbp(y)}")
    return reform, [
        x * wa_adult_coef,
        x * child_coef,
        x * adult_disability_coef,
        x * child_disability_coef,
        x_hist,
        y_hist,
    ]
