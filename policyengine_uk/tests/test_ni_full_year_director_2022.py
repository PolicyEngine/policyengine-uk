"""The declared 2022–23 annual employee schedule, not interim director payroll."""

from pathlib import Path

import numpy as np
import pytest
from policyengine_core.parameters import load_parameter_file

import policyengine_uk
from policyengine_uk import CountryTaxBenefitSystem, Simulation
from policyengine_uk.utils.scenario import Scenario

pytestmark = pytest.mark.usefixtures("cloned_uk_tax_benefit_system")
DIRECTORS = "gov.hmrc.national_insurance.class_1.directors.full_year_category_a_2022_23"
DIRECTORY = (
    Path(policyengine_uk.__file__).parent
    / "parameters/gov/hmrc/national_insurance/class_1/directors/full_year_category_a_2022_23"
)
COMPONENTS = (
    "ni_class_1_employee_primary",
    "ni_class_1_employee_additional",
    "ni_class_1_employee",
)


def situation(year=2022, flags=(True,), earnings=(30000,), age=40):
    people = {}
    for i, earnings_i in enumerate(earnings):
        people[f"p{i}"] = {
            "age": {year: age},
            "employment_income": {year: earnings_i},
        }
        if flags[i] is not None:
            people[f"p{i}"]["is_full_year_category_a_director"] = {year: flags[i]}
    return {
        "people": people,
        "benunits": {f"b{i}": {"members": [p]} for i, p in enumerate(people)},
        "households": {"h": {"members": list(people)}},
    }


def test_raw_coverage_and_scale_metadata():
    coverage = load_parameter_file(str(DIRECTORY / "in_effect.yaml"), "in_effect")
    for date, expected in [
        ("2022-04-05", False),
        ("2022-04-06", True),
        ("2023-04-05", True),
        ("2023-04-06", False),
    ]:
        assert coverage(date) == expected
    scale = load_parameter_file(
        str(DIRECTORY / "employee_scale.yaml"), "employee_scale"
    )
    assert scale.metadata["threshold_unit"] == "currency-GBP"
    assert scale.metadata["rate_unit"] == "/1"
    assert scale.metadata["reference"]
    assert not scale.metadata.get("uprating")
    for bracket, threshold, rate in zip(
        scale.brackets, [0, 11908, 50270], [0, 0.1273, 0.0273]
    ):
        assert bracket.threshold("2022-04-06") == threshold
        assert bracket.rate("2022-04-06") == rate
        for leaf in (bracket.threshold, bracket.rate):
            assert [v.instant_str for v in leaf.values_list] == ["2022-04-06"]
            assert not leaf.metadata.get("uprating")


def test_processed_gate_and_input_metadata():
    system = CountryTaxBenefitSystem()
    for year, active in [(2021, False), (2022, True), (2023, False), (2030, False)]:
        node = system.parameters(
            str(year)
        ).gov.hmrc.national_insurance.class_1.directors
        assert node.full_year_category_a_2022_23.in_effect == active
    scale = system.parameters("2022").gov.hmrc.national_insurance.class_1.directors
    assert scale.full_year_category_a_2022_23.employee_scale.thresholds == [
        0,
        11908,
        50270,
    ]
    assert scale.full_year_category_a_2022_23.employee_scale.rates == [
        0,
        0.1273,
        0.0273,
    ]
    variable = system.variables["is_full_year_category_a_director"]
    assert variable.default_value is False
    assert variable.value_type is bool
    assert "2022–23 only" in variable.label


@pytest.mark.parametrize("year", [2021, 2022, 2023, 2026])
def test_default_false_and_out_of_year_true_preserve_ordinary(year):
    baseline = Simulation(situation=situation(year, (None,)))
    false = Simulation(situation=situation(year, (False,)))
    true = Simulation(situation=situation(year, (True,)))
    for variable in (*COMPONENTS, "ni_class_1_employer"):
        expected = baseline.calculate(variable, year)
        np.testing.assert_array_equal(false.calculate(variable, year), expected)
        if year != 2022 or variable == "ni_class_1_employer":
            np.testing.assert_array_equal(true.calculate(variable, year), expected)


def test_monthly_allocation_components_person_mask_and_query_order():
    data = situation(flags=(True, True, False), earnings=(30000, 60000, 30000))
    first = Simulation(situation=data)
    second = Simulation(situation=data)
    expected = [2303.1116, 5149.1116, 2665.9]
    # Query the final total first, then reverse the component query order.
    np.testing.assert_allclose(
        first.calculate(COMPONENTS[2], 2022), expected, atol=0.01
    )
    additional = second.calculate(COMPONENTS[1], 2022)
    primary = second.calculate(COMPONENTS[0], 2022)
    np.testing.assert_allclose(primary + additional, expected, atol=0.01)
    np.testing.assert_allclose(
        second.calculate(COMPONENTS[2], 2022), expected, atol=0.01
    )
    for variable in COMPONENTS:
        months = [
            first.calculate(variable, f"2022-{month:02d}") for month in range(1, 13)
        ]
        np.testing.assert_allclose(
            sum(months), first.calculate(variable, 2022), atol=0.01
        )
        # Equal allocations follow annual inputs; they are not observed payroll cash.
        for month in months[1:]:
            np.testing.assert_array_equal(month, months[0])


def test_previous_year_fact_does_not_extend_implementation_coverage():
    data = situation()
    data["people"]["p0"]["age"][2023] = 41
    data["people"]["p0"]["employment_income"][2023] = 30000
    sim = Simulation(situation=data)
    baseline = Simulation(situation=situation(2023, (None,)))
    np.testing.assert_array_equal(
        sim.calculate("ni_class_1_employee", 2023),
        baseline.calculate("ni_class_1_employee", 2023),
    )


@pytest.mark.parametrize("age", [15, 80])
def test_existing_final_age_gate_remains_authoritative(age):
    # Inconsistent declared status deliberately tests composition, not entitlement.
    sim = Simulation(situation=situation(age=age))
    assert sim.calculate("ni_class_1_employee", 2022)[0] == 0


def test_ni_earnings_composition_is_not_replaced_with_salary():
    data = situation(earnings=(28000,))
    data["people"]["p0"].update(
        statutory_sick_pay={2022: 2000},
        employee_pension_contributions_reported={2022: 1000},
    )
    sim = Simulation(situation=data)
    assert sim.calculate("ni_class_1_income", 2022)[0] == 30000
    assert sim.calculate("ni_class_1_employee", 2022)[0] == pytest.approx(
        2303.1116, abs=0.01
    )


def test_explicit_final_input_remains_authoritative():
    data = situation()
    data["people"]["p0"]["ni_class_1_employee"] = {2022: 123}
    sim = Simulation(situation=data)
    assert sim.calculate("ni_class_1_employee", 2022)[0] == pytest.approx(123, abs=0.01)


def test_director_scale_reform_changes_only_the_declared_route():
    data = situation(flags=(True, False), earnings=(30000, 30000))

    def reform_schedule(simulation):
        system = simulation.tax_benefit_system
        system.reset_parameters()
        scale = system.parameters.gov.hmrc.national_insurance.class_1.directors
        scale.full_year_category_a_2022_23.employee_scale.brackets[1].rate.update(
            period="year:2022-01-01:1", value=0.2
        )
        system.process_parameters()

    sim = Simulation(
        situation=data,
        scenario=Scenario(
            simulation_modifier=reform_schedule, applied_before_data_load=True
        ),
    )
    np.testing.assert_allclose(
        sim.calculate("ni_class_1_employee", 2022), [3618.4, 2665.9], atol=0.01
    )


def test_natural_cash_support_is_unchanged_by_director_status():
    # This is the existing model's calendar-2022 support, not a new rate rule.
    values = []
    other_taxes = []
    for flag, ni in [(False, 2665.9), (True, 2303.1116)]:
        data = situation(flags=(flag,))
        data["benunits"]["b0"]["would_claim_uc"] = {2022: False}
        data["households"]["h"]["region"] = {2022: "LONDON"}
        data["households"]["h"]["household_owns_tv"] = {2022: False}
        sim = Simulation(situation=data)
        assert sim.calculate("ebr_council_tax_rebate", 2022)[0] == 150
        assert sim.calculate("ebr_energy_bills_credit", 2022)[0] == 199
        assert sim.calculate("household_benefits", 2022)[0] == 349
        assert sim.calculate("tv_licence", 2022)[0] == 0
        assert sim.calculate("income_tax", 2022)[0] == 3486
        assert sim.calculate("national_insurance", 2022)[0] == pytest.approx(
            ni, abs=0.01
        )
        actual_cash = sim.calculate("household_net_income", 2022)[0]
        other_taxes.append(float(sim.calculate("household_tax", 2022)[0]) - ni)
        values.append(float(actual_cash))
    # Only employee NI changes: the literal cash gain equals the NI reduction.
    # Tolerance reflects float32 household totals, without a payroll rounding rule.
    assert values[1] - values[0] == pytest.approx(362.7884, abs=0.01)
    assert other_taxes[0] == pytest.approx(other_taxes[1], abs=0.01)


def test_director_primary_propagates_through_existing_class_4_cap():
    """Composition of existing rules, not a new standalone Class 4 law oracle."""
    results = []
    # Profit is net of £2,000 expenses: gross receipts exceed profit by more
    # than the trading allowance. No loss, capital allowance or output is supplied.
    for flag, primary, cap, total_ni in [
        (False, 2665.9, 2082.6041179856, 4912.3041179856),
        (True, 2303.1116, 2343.6029669065, 4810.5145669065),
    ]:
        data = situation(flags=(flag,))
        data["people"]["p0"].update(
            self_employment_income={2022: 60000},
            self_employment_gross_receipts={2022: 62000},
        )
        data["benunits"]["b0"]["would_claim_uc"] = {2022: False}
        data["households"]["h"].update(
            region={2022: "LONDON"}, household_owns_tv={2022: False}
        )
        sim = Simulation(situation=data)
        assert sim.calculate("trading_allowance_deduction", 2022)[0] == 0
        assert sim.calculate("ni_class_4_profits", 2022)[0] == 60000
        assert sim.calculate("ni_class_1_employee_primary", 2022)[0] == pytest.approx(
            primary, abs=0.01
        )
        assert sim.calculate("ni_class_1_employee_additional", 2022)[0] == 0
        assert sim.calculate("ni_class_2", 2022)[0] == pytest.approx(163.8, abs=0.01)
        # Existing 2022 parameters: UPL50270, LPL11908, Class4rates.0973/.0273,
        # Class2weekly3.15. AboveUPL, case1false. Headroom =38362*.0973
        # +53*3.15 -52*3.15 -primary. Remaining main band is charged at.0273.
        assert sim.calculate("ni_class_4_maximum", 2022)[0] == pytest.approx(
            cap, abs=0.01
        )
        assert cap < 3998.2516  # Uncapped Class 4:38362*.0973+9730*.0273.
        assert sim.calculate("ni_class_4", 2022)[0] == pytest.approx(cap, abs=0.01)
        assert sim.calculate("national_insurance", 2022)[0] == pytest.approx(
            total_ni, abs=0.01
        )
        results.append(
            {
                variable: float(sim.calculate(variable, 2022)[0])
                for variable in [
                    "household_net_income",
                    "household_benefits",
                    "income_tax",
                    "ni_class_1_employer",
                ]
            }
        )
    for variable in ["household_benefits", "income_tax", "ni_class_1_employer"]:
        assert results[0][variable] == pytest.approx(results[1][variable], abs=0.01)
    # Class 1 falls362.7884, Class4rises260.9988489; final cash gain is101.7895511.
    assert results[1]["household_net_income"] - results[0][
        "household_net_income"
    ] == pytest.approx(101.7895511, abs=0.01)
