import pandas as pd
import pytest

from policyengine_uk import Simulation
from policyengine_uk.data.dataset_schema import (
    UKMultiYearDataset,
    UKSingleYearDataset,
)
from policyengine_uk.scenarios import no_economic_assumptions


def test_no_economic_assumptions_freezes_growthfactor_uprating():
    situation = {
        "people": {
            "person": {
                "age": {2025: 40},
                "employment_income": {2025: 30_000},
            }
        },
        "benunits": {"benunit": {"members": ["person"]}},
        "households": {"household": {"members": ["person"]}},
    }

    baseline = Simulation(situation=situation)
    reformed = Simulation(situation=situation, scenario=no_economic_assumptions)

    baseline_income_2025 = float(baseline.calculate("employment_income", 2025)[0])
    baseline_income_2026 = float(baseline.calculate("employment_income", 2026)[0])
    reformed_income_2025 = float(reformed.calculate("employment_income", 2025)[0])
    reformed_income_2026 = float(reformed.calculate("employment_income", 2026)[0])

    assert baseline_income_2026 > baseline_income_2025
    assert reformed_income_2026 == pytest.approx(reformed_income_2025)

    baseline_fees = baseline.tax_benefit_system.parameters.gov.simulation.private_school_vat.private_school_fees
    reformed_fees = reformed.tax_benefit_system.parameters.gov.simulation.private_school_vat.private_school_fees
    assert float(baseline_fees("2026")) > float(baseline_fees("2025"))
    assert float(reformed_fees("2026")) == pytest.approx(float(reformed_fees("2025")))

    baseline_benefit_index = (
        baseline.tax_benefit_system.parameters.gov.benefit_uprating_cpi
    )
    reformed_benefit_index = (
        reformed.tax_benefit_system.parameters.gov.benefit_uprating_cpi
    )
    assert float(baseline_benefit_index("2026")) > float(baseline_benefit_index("2025"))
    assert float(reformed_benefit_index("2026")) == pytest.approx(
        float(reformed_benefit_index("2025"))
    )


def test_no_economic_assumptions_resets_multi_year_dataset_without_mutating_input():
    person_2025 = pd.DataFrame(
        {
            "person_id": [1],
            "person_benunit_id": [1],
            "person_household_id": [1],
            "employment_income": [30_000.0],
            "age": [40],
        }
    )
    person_2026 = person_2025.copy()
    person_2026["employment_income"] = [31_019.96875]
    person_2026["age"] = [41]

    benunit = pd.DataFrame({"benunit_id": [1]})
    household = pd.DataFrame({"household_id": [1]})

    dataset = UKMultiYearDataset(
        datasets=[
            UKSingleYearDataset(
                person=person_2025,
                benunit=benunit.copy(),
                household=household.copy(),
                fiscal_year=2025,
            ),
            UKSingleYearDataset(
                person=person_2026,
                benunit=benunit.copy(),
                household=household.copy(),
                fiscal_year=2026,
            ),
        ]
    )

    baseline = Simulation(dataset=dataset)
    reformed = Simulation(dataset=dataset, scenario=no_economic_assumptions)

    assert float(baseline.calculate("employment_income", 2026)[0]) == pytest.approx(
        31_019.96875
    )
    assert float(reformed.calculate("employment_income", 2026)[0]) == pytest.approx(
        30_000.0
    )
    assert int(reformed.calculate("age", 2026)[0]) == 41
    assert dataset[2026].person["employment_income"].iloc[0] == pytest.approx(
        31_019.96875
    )
