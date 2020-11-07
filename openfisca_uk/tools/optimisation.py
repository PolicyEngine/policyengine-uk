from openfisca_uk.tools.simulation import model
from scipy.optimize import differential_evolution
from openfisca_core.model_api import *
from openfisca_uk.entities import *
import numpy as np


def cost_of_reform(reform, period="2020-10-25"):
    baseline = model(period=period)
    reformed = model(reform, period=period)
    benunits = baseline.calculate("benunit_weight", period)
    net_cost = np.sum(
        (
            reformed.calculate("benunit_net_income", period)
            - baseline.calculate("benunit_net_income", period)
        )
        * benunits
    )
    return net_cost


def poverty_reduction(reform, period="2020-10-25"):
    baseline = model(period=period)
    reformed = model(reform, period=period)
    households = baseline.calculate("household_weight", period)
    poverty_baseline = np.average(
        baseline.calculate("in_poverty_bhc", period), weights=households
    )
    poverty_reformed = np.average(
        reformed.calculate("in_poverty_bhc", period), weights=households
    )
    poverty_reduction = (
        poverty_baseline - poverty_reformed
    ) / poverty_baseline
    return poverty_reduction


def optimal_basic_income():
    def loss(x):
        flat_tax_rate, senior_amount, adult_amount, child_amount = x

        class income_tax(Variable):
            value_type = float
            entity = Person
            label = u"Income tax paid per week"
            definition_period = ETERNITY

            def formula(person, period, parameters):
                return flat_tax_rate * person(
                    "income_tax_applicable_amount", period
                )

        class basic_income(Variable):
            value_type = float
            entity = Person
            label = u"Amount of basic income received per week"
            definition_period = ETERNITY

            def formula(person, period, parameters):
                seniors = person("is_senior", period)
                WA_adults = person("is_working_age_adult", period)
                children = person("is_child", period)
                return (
                    senior_amount * seniors
                    + adult_amount * WA_adults
                    + child_amount * children
                )

        class benunit_basic_income(Variable):
            value_type = float
            entity = BenUnit
            label = u"Amount of basic income per week for the benefit unit"
            definition_period = ETERNITY

            def formula(benunit, period, parameters):
                return benunit.sum(benunit.members("basic_income", period))

        class non_means_tested_bonus(Variable):
            value_type = float
            entity = Person
            label = u"Amount of the basic income which is not subject to means tests"
            definition_period = ETERNITY

            def formula(person, period, parameters):
                return person("basic_income", period)

        class basic_income_reform(Reform):
            def apply(self):
                for changed_var in [income_tax, non_means_tested_bonus]:
                    self.update_variable(changed_var)
                for added_var in [basic_income, benunit_basic_income]:
                    self.add_variable(added_var)
                for removed_var in [
                    "NI",
                    "child_benefit",
                    "income_support",
                    "JSA_contrib",
                    "JSA_income",
                    "child_tax_credit",
                    "working_tax_credit",
                    "universal_credit",
                    "state_pension",
                    "housing_benefit",
                    "pension_credit",
                    "ESA_income",
                ]:
                    self.neutralize_variable(removed_var)

        cost = cost_of_reform(basic_income_reform)
        poverty_impact = poverty_reduction(basic_income_reform)
        print(x, cost, poverty_impact)
        return cost - poverty_impact * 1e11

    solution = differential_evolution(
        loss, [(0, 1), (0, 200), (0, 200), (0, 200)]
    )
    return solution
