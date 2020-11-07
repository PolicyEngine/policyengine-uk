from openfisca_core.model_api import *
from openfisca_uk.entities import *
from openfisca_uk.tools.simulation import model
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
    class income_tax_applicable_amount(Variable):
        value_type = float
        entity = Person
        label = u"Total taxable income per week"
        definition_period = ETERNITY

        def formula(person, period, parameters):
            return max_(
                person("employee_earnings", period)
                + person("self_employed_earnings", period)
                + person("state_pension", period)
                + person("pension_income", period)
                + person("taxed_means_tested_bonus", period)
                + person("interest", period),
                0,
            )

    class income_tax(Variable):
        value_type = float
        entity = Person
        label = u"Income tax paid per week"
        definition_period = ETERNITY

        def formula(person, period, parameters):
            return flat_tax_rate * person(
                "income_tax_applicable_amount", period
            )

    class NI(Variable):
        value_type = float
        entity = Person
        label = u"National Insurance paid per week"
        definition_period = ETERNITY
        reference = ["https://www.gov.uk/national-insurance"]

        def formula(person, period, parameters):
            return 0

    class basic_income(Variable):
        value_type = float
        entity = Person
        label = u"Amount of basic income received per week"
        definition_period = ETERNITY

        def formula(person, period, parameters):
            return (
                pensioner_amount * person("basic_income_pensioner", period)
                + wa_adult_amount * person("basic_income_wa_adult", period)
                + child_amount * person("basic_income_u18", period)
                + person("disabled", period)
                * person("basic_income_adult", period)
                * adult_disability_bonus
                + person("disabled", period)
                * person("basic_income_u18", period)
                * child_disability_bonus
            )

    class benunit_basic_income(Variable):
        value_type = float
        entity = BenUnit
        label = u"Amount of basic income per week for the benefit unit"
        definition_period = ETERNITY

        def formula(benunit, period, parameters):
            return benunit.sum(benunit.members("basic_income", period))

    class household_basic_income(Variable):
        value_type = float
        entity = Household
        label = u"Amount of basic income per week for the benefit unit"
        definition_period = ETERNITY

        def formula(household, period, parameters):
            return household.sum(household.members("basic_income", period))

    class non_means_tested_bonus(Variable):
        value_type = float
        entity = Person
        label = (
            u"Amount of the basic income which is not subject to means tests"
        )
        definition_period = ETERNITY

        def formula(person, period, parameters):
            return person("basic_income", period)

    class reform(Reform):
        def apply(self):
            for changed_var in [
                income_tax,
                income_tax_applicable_amount,
                NI,
                non_means_tested_bonus,
            ]:
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


def net_cost_of_reform(reform, period="2020-10-25"):
    baseline = model(period=period)
    reformed = model(reform, period=period)
    households = baseline.calculate("household_weight", period)
    net_cost = (
        np.sum(
            (
                reformed.calculate("household_net_income_ahc", period)
                - baseline.calculate("household_net_income_ahc", period)
            )
            * households
        )
        * 52
    )
    return net_cost


def solve_ft_ubi_reform(
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
    y = net_cost_of_reform(reform)
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
    return reform, [
        x * wa_adult_coef,
        x * child_coef,
        x * adult_disability_coef,
        x * child_disability_coef,
        x_hist,
        y_hist,
    ]
