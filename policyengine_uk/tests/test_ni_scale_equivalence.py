"""Differential against frozen original NI formulas, plus independent cash oracles.

The original formula sources are from UK e1601dbe4feb15e71d0d59b7a57f9d860741c068.
They restore only those formulas on the same parameter/input tree, not an entire
old model or historical legal entitlement. Parameter histories and metadata have
separate exact pre-migration fixtures; malformed reforms are compatibility tests.
"""

import numpy as np
import pytest
from policyengine_core.reforms import Reform
from policyengine_uk import Simulation
from policyengine_uk.utils.scenario import Scenario

ORIGINAL_SOURCES = {
    "policyengine_uk/variables/gov/hmrc/national_insurance/class_1/ni_class_1_employee_primary.py": 'from policyengine_uk.model_api import *\n\n\nclass ni_class_1_employee_primary(Variable):\n    label = "NI Class 1 employee-side primary contributions"\n    entity = Person\n    definition_period = MONTH\n    value_type = float\n    unit = GBP\n    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/8"\n\n    def formula(person, period, parameters):\n        income = person("ni_class_1_income", period)\n        parameters = parameters(period).gov.hmrc.national_insurance.class_1\n\n        # Thresholds are weekly, so multiply by weeks in year and divide by months in year\n        primary_threshold = (\n            parameters.thresholds.primary_threshold * WEEKS_IN_YEAR / MONTHS_IN_YEAR\n        )\n        upper_earnings_limit = (\n            parameters.thresholds.upper_earnings_limit * WEEKS_IN_YEAR / MONTHS_IN_YEAR\n        )\n\n        upper_earnings_limit_income = max_(income - upper_earnings_limit, 0)\n        primary_threshold_income = (\n            max_(income - primary_threshold, 0) - upper_earnings_limit_income\n        )\n\n        return parameters.rates.employee.main * primary_threshold_income\n',
    "policyengine_uk/variables/gov/hmrc/national_insurance/class_1/ni_class_1_employee_additional.py": 'from policyengine_uk.model_api import *\n\n\nclass ni_class_1_employee_additional(Variable):\n    label = "NI Class 1 employee-side additional contributions"\n    entity = Person\n    definition_period = MONTH\n    value_type = float\n    unit = GBP\n    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/8"\n\n    def formula(person, period, parameters):\n        income = person("ni_class_1_income", period)\n        parameters = parameters(period).gov.hmrc.national_insurance.class_1\n        upper_earnings_limit = (\n            parameters.thresholds.upper_earnings_limit * WEEKS_IN_YEAR / MONTHS_IN_YEAR\n        )\n        upper_earnings_limit_income = max_(income - upper_earnings_limit, 0)\n        return parameters.rates.employee.additional * upper_earnings_limit_income\n',
    "policyengine_uk/variables/gov/hmrc/national_insurance/class_1/ni_class_1_employer.py": 'from policyengine_uk.model_api import *\n\n\nclass ni_class_1_employer(Variable):\n    value_type = float\n    entity = Person\n    label = "NI Class 1 employer-side contributions"\n    definition_period = YEAR\n    unit = GBP\n    defined_for = "ni_class_1_secondary_liable"\n    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/9"\n\n    def formula(person, period, parameters):\n        class_1 = parameters(period).gov.hmrc.national_insurance.class_1\n        earnings = person("ni_class_1_income", period)\n        if not parameters(\n            period\n        ).gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions:\n            added_pension_contributions = person(\n                "employer_pension_contributions", period\n            )\n            taxed_earnings = earnings + added_pension_contributions\n        else:\n            taxed_earnings = earnings\n        secondary_threshold = class_1.thresholds.secondary_threshold * WEEKS_IN_YEAR\n        main_earnings = max_(\n            taxed_earnings - secondary_threshold,\n            0,\n        )\n        return class_1.rates.employer * main_earnings\n',
    "policyengine_uk/variables/gov/hmrc/national_insurance/class_4/ni_class_4.py": 'from policyengine_uk.model_api import *\n\n\nclass ni_class_4(Variable):\n    value_type = float\n    entity = Person\n    label = "NI Class 4 contributions"\n    definition_period = YEAR\n    unit = GBP\n    defined_for = "ni_class_4_liable"\n    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/15"\n\n    def formula(person, period, parameters):\n        class_4 = parameters(period).gov.hmrc.national_insurance.class_4\n        # Schedule 2: Class 4 is charged on the Chapter 2 trade profits less\n        # the para 3 loss reliefs; Class 1 contributions are not a deduction.\n        profits = person("ni_class_4_profits", period)\n        add_rate_income = max_(\n            profits - class_4.thresholds.upper_profits_limit,\n            0,\n        )\n        main_rate_income = (\n            max_(\n                profits - class_4.thresholds.lower_profits_limit,\n                0,\n            )\n            - add_rate_income\n        )\n        pre_maximum_amount = (\n            main_rate_income * class_4.rates.main\n            + add_rate_income * class_4.rates.additional\n        )\n        maximum_amount = person("ni_class_4_maximum", period)\n        # Regulation 100(1): the annual maximum applies only where primary\n        # Class 1 (or, before 6 April 2024, Class 2) contributions are also\n        # payable for the year.\n        includes_class_2 = class_4.annual_maximum.includes_class_2\n        maximum_applies = (person("ni_class_1_employee", period) > 0) | np.logical_and(\n            includes_class_2, person("ni_class_2", period) > 0\n        )\n        return max_(\n            where(\n                maximum_applies,\n                min_(pre_maximum_amount, maximum_amount),\n                pre_maximum_amount,\n            ),\n            0,\n        )\n',
    "policyengine_uk/variables/gov/hmrc/national_insurance/class_4/ni_class_4_main.py": 'from policyengine_uk.model_api import *\n\n\nclass ni_class_4_main(Variable):\n    value_type = float\n    entity = Person\n    label = "NI Class 4 main contributions"\n    definition_period = YEAR\n    unit = GBP\n    defined_for = "ni_class_4_liable"\n    reference = "https://www.legislation.gov.uk/ukpga/1992/4/section/15"\n\n    def formula(person, period, parameters):\n        class_4 = parameters(period).gov.hmrc.national_insurance.class_4\n        profits = person("ni_class_4_profits", period)\n        add_rate_income = max_(\n            profits - class_4.thresholds.upper_profits_limit,\n            0,\n        )\n        main_rate_income = (\n            max_(\n                profits - class_4.thresholds.lower_profits_limit,\n                0,\n            )\n            - add_rate_income\n        )\n        return main_rate_income * class_4.rates.main\n',
    "policyengine_uk/variables/gov/hmrc/national_insurance/class_4/ni_class_4_maximum.py": 'from policyengine_uk.model_api import *\n\n\nclass ni_class_4_maximum(Variable):\n    label = "NI Class 4 maximum liability"\n    entity = Person\n    definition_period = YEAR\n    value_type = float\n    unit = GBP\n    reference = "https://www.legislation.gov.uk/uksi/2001/1004/regulation/100"\n\n    def formula(person, period, parameters):\n        ni = parameters(period).gov.hmrc.national_insurance\n        upl = ni.class_4.thresholds.upper_profits_limit\n        lpl = ni.class_4.thresholds.lower_profits_limit\n        step_1 = upl - lpl\n        # Regulation 100 writes its percentages out, but in every year from\n        # 2015-16 they match the Class 4 rates: 9% and 2% (Steps Two, Five,\n        # Eight and Nine) to 2021-22 and in 2023-24; 9.73% and 2.73% for\n        # 2022-23 (Health and Social Care Levy (Repeal) Act 2022 Sch para\n        # 6(2)); from 2024-25, 6% and 100/6 in Steps Two and Five (National\n        # Insurance Contributions (Reduction in Rates) Act 2024 s 2(3)) with\n        # Steps Eight and Nine still at 2%. So the steps read the rate\n        # parameters.\n        main_rate = ni.class_4.rates.main\n        add_rate = ni.class_4.rates.additional\n        step_2 = step_1 * main_rate\n        # Class 2 contributions drop out of regulation 100 from 6 April 2024.\n        includes_class_2 = ni.class_4.annual_maximum.includes_class_2\n        class_2_weeks_addition = 53 * ni.class_2.flat_rate * includes_class_2\n        step_3 = step_2 + class_2_weeks_addition\n        class_2_contributions = person("ni_class_2", period) * includes_class_2\n        primary_class_1_contributions = person("ni_class_1_employee_primary", period)\n        step_4_raw = step_3 - class_2_contributions - primary_class_1_contributions\n        step_4 = max_(step_4_raw, 0)\n        # Case 1: Step Four exceeds primary Class 1 + Class 2 + main-rate\n        # Class 4. Main-rate Class 4 is Step Two less the main rate on the\n        # unused part of the main band, so this is equivalent to\n        #   main rate x unused band + 53 weekly Class 2 rates\n        #     > 2 x (primary Class 1 + Class 2).\n        # Comparing the totals directly left the case to float32 rounding\n        # when they were equal (profits above the UPL, no Class 1 or 2), and\n        # a wrong Case 1 dropped the additional-rate band (#1878). The unused\n        # band is exactly zero at or above the UPL, so that equality is now\n        # decided exactly.\n        profits = person("ni_class_4_profits", period)\n        unused_main_band = clip(upl - profits.astype(np.float64), 0, step_1)\n        case_1 = (step_4_raw >= 0) & (\n            main_rate * unused_main_band + class_2_weeks_addition\n            > 2\n            * (\n                class_2_contributions.astype(np.float64)\n                + primary_class_1_contributions.astype(np.float64)\n            )\n        )\n        # Step Five converts Step Four back to profits at the main rate. With a\n        # zero main rate (a reform abolishing it) there is no main-rate\n        # liability to limit, so the headroom is unlimited instead of 0 / 0.\n        step_5 = np.divide(\n            step_4,\n            main_rate,\n            out=np.full_like(step_4, np.inf),\n            where=main_rate > 0,\n        )\n        step_6 = min_(upl, profits) - lpl\n        step_7 = max_(0, step_6 - step_5)\n        step_8 = step_7 * add_rate\n        step_9 = max_(0, profits - upl) * add_rate\n\n        return where(case_1, step_4, step_4 + step_8 + step_9)\n',
}

ORIGINAL_CLASSES = []
for source_path, source in ORIGINAL_SOURCES.items():
    namespace = {}
    exec(compile(source, source_path, "exec"), namespace)
    ORIGINAL_CLASSES.append(namespace[source_path.rsplit("/", 1)[-1][:-3]])


class OriginalNIFormulas(Reform):
    def apply(self):
        for variable in ORIGINAL_CLASSES:
            self.update_variable(variable)


def situation():
    facts = [(40, 30000, 0), (40, 60000, 18000), (70, 12000, 70000), (40, 0, 20000)]
    people = {
        f"p{i}": {
            "age": {2026: age},
            "employment_income": {2026: wage},
            "self_employment_income": {2026: profit},
        }
        for i, (age, wage, profit) in enumerate(facts)
    }
    return {
        "people": people,
        "benunits": {f"b{i}": {"members": [f"p{i}"]} for i in range(len(facts))},
        "households": {
            f"h{i}": {
                "members": [f"p{i}"],
                "region": {2026: "LONDON"},
                "tenure_type": {2026: "OWNED_OUTRIGHT"},
                "council_tax": {2026: 0},
            }
            for i in range(len(facts))
        },
    }


PREFIX = "gov.hmrc.national_insurance."
REFORMS = [
    {},
    {PREFIX + "class_1.rates.employee.main": {"2026": 0}},
    {
        PREFIX + "class_1.thresholds.primary_threshold": {"2026": 200},
        PREFIX + "class_1.thresholds.upper_earnings_limit": {"2026": 200},
    },
    {
        PREFIX + "class_1.thresholds.primary_threshold": {"2026": 300},
        PREFIX + "class_1.thresholds.upper_earnings_limit": {"2026": 200},
    },
    {
        PREFIX + "class_4.thresholds.lower_profits_limit": {"2026": 20000},
        PREFIX + "class_4.thresholds.upper_profits_limit": {"2026": 10000},
    },
    {
        "gov.contrib.policyengine.employer_ni.exempt_employer_pension_contributions": {
            "2026": False
        }
    },
]


@pytest.mark.parametrize("changes", REFORMS)
def test_component_and_final_cash_equal_frozen_original_formulas(changes):
    current = Simulation(situation=situation(), scenario=Scenario.from_reform(changes))
    original = Simulation(
        situation=situation(),
        scenario=Scenario.from_reform((OriginalNIFormulas, changes)),
    )
    outputs = [
        "ni_class_1_employee_primary",
        "ni_class_1_employee_additional",
        "ni_class_1_employee",
        "ni_class_1_employer",
        "ni_class_4_main",
        "ni_class_4_maximum",
        "ni_class_4",
        "national_insurance",
        "household_net_income",
    ]
    for name in outputs:
        expected = original.calculate(name, 2026)
        actual = current.calculate(name, 2026)
        np.testing.assert_array_equal(actual, expected, err_msg=name)
        assert actual.dtype == expected.dtype
    # Query order cannot change a later output or the independent source system.
    np.testing.assert_array_equal(
        current.calculate("household_net_income", 2026),
        original.calculate("household_net_income", 2026),
    )


def test_natural_2026_independent_ni_cash_examples():
    sim = Simulation(situation=situation())
    np.testing.assert_allclose(
        sim.calculate("ni_class_1_employee", 2026),
        [1394.4032, 3210.6008, 0, 0],
        atol=0.002,
        rtol=0,
    )
    np.testing.assert_allclose(
        sim.calculate("ni_class_1_employer", 2026),
        [3750, 8250, 1050, 0],
        atol=0.002,
        rtol=0,
    )
    assert float(sim.calculate("ni_class_4", 2026)[3]) == pytest.approx(
        445.8, abs=0.002
    )


@pytest.mark.parametrize("route", ["dict", "core", "changes"])
def test_scalar_and_canonical_leaf_reforms_have_same_natural_final_path(route):
    old = {PREFIX + "class_1.rates.employee.main": {"2026": 0.1}}
    new = {PREFIX + "class_1.employee_scale[1].rate": {"2026": 0.1}}

    def scenario(values):
        if route == "changes":
            return Scenario(parameter_changes=values)
        if route == "core":
            return Scenario.from_reform(Reform.from_dict(values))
        return Scenario.from_reform(values)

    a = Simulation(situation=situation(), scenario=scenario(old))
    b = Simulation(situation=situation(), scenario=scenario(new))
    np.testing.assert_array_equal(
        a.calculate("ni_class_1_employee", 2026),
        b.calculate("ni_class_1_employee", 2026),
    )
    np.testing.assert_array_equal(
        a.calculate("household_net_income", 2026),
        b.calculate("household_net_income", 2026),
    )
